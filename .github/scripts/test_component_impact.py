"""Behavioral impact contracts, exercised through actual temporary Git histories."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import sys
import textwrap
import unittest

import component_impact as impact


def spec(paths, dependencies=(), checks=()):
    return {'paths': paths, 'depends_on': list(dependencies), 'checks': list(checks)}


def manifest():
    return {'version': 1, 'global_paths': ['toolchain.lock'], 'components': {
        'api': spec(['api/'], checks=['routing']),
        'web': spec(['web/'], ['api'], ['profiles']),
        'worker': spec(['worker/'], checks=['cleanup'])}}


class ImpactTests(unittest.TestCase):
    def test_transitive_dependents_are_selected(self):
        data = manifest()
        data['components']['e2e'] = spec(['e2e/'], ['web'], ['epics'])
        result = impact.affected(data, ['api/schema.json'])
        self.assertFalse(result['full'])
        self.assertEqual(result['components'], ['api', 'e2e', 'web'])
        self.assertEqual(result['checks'], ['epics', 'profiles', 'routing'])
        self.assertEqual(impact.affected(data, ['web/view.py'])['components'], ['e2e', 'web'])

    def test_unknown_and_global_inputs_run_everything(self):
        for path in ['new-app/file', 'toolchain.lock', impact.MANIFEST, 'AGENTS.md',
                     '.github/workflows/new.yml', '.github/scripts/component_impact.py']:
            with self.subTest(path=path):
                result = impact.affected(manifest(), [path])
                self.assertTrue(result['full'])
                self.assertEqual(result['components'], ['api', 'web', 'worker'])

    def test_prefix_boundaries_and_overlapping_owners(self):
        data = manifest()
        self.assertTrue(impact.affected(data, ['api-other/x'])['full'])
        data['components']['worker']['paths'].append('api/')
        self.assertEqual(impact.affected(data, ['api/x'])['components'], ['api', 'web', 'worker'])

    def test_empty_changes_and_no_manifest(self):
        self.assertEqual(impact.affected(manifest(), [])['checks'], [])
        self.assertTrue(impact.affected(None, [])['full'])

    def test_schema_rejects_cycles_unknown_fields_and_unsafe_paths(self):
        cases = []
        for value in [True, 2, '1']:
            data = manifest(); data['version'] = value; cases.append(data)
        data = manifest(); data['ignored_paths'] = ['api/']; cases.append(data)
        data = manifest(); data['components']['api']['depends_on'] = ['web']; cases.append(data)
        data = manifest(); data['components']['api']['depends_on'] = ['missing']; cases.append(data)
        for path in ['../api/', '/api/', 'api//x', 'api/*', 'api/./x', '']:
            data = manifest(); data['components']['api']['paths'] = [path]; cases.append(data)
        for data in cases:
            with self.subTest(data=data), self.assertRaises(impact.ImpactError):
                impact.validate_manifest(data)

    def test_duplicate_json_keys_are_not_last_writer_wins(self):
        with self.assertRaises(impact.ImpactError):
            json.loads('{"version":1,"version":2}', object_pairs_hook=impact.unique_object)

    def test_ci_always_runs_planner_contract_and_rejects_unknown_checks(self):
        selected = impact.ci_selection({'full': False, 'checks': ['cleanup']})
        self.assertEqual({name for name, run in selected.items() if run}, {'cleanup', 'components'})
        self.assertTrue(all(impact.ci_selection({'full': True}).values()))
        for report in [{'full': 'false'}, {'full': False, 'checks': ['unregistered']}, {}]:
            with self.subTest(report=report), self.assertRaises(impact.ImpactError):
                impact.ci_selection(report)

    def test_canonical_manifest_only_names_supported_checks(self):
        path = Path(__file__).resolve().parents[2] / impact.MANIFEST
        if not path.exists() and not path.is_symlink():
            self.skipTest('Optional manifest absent; conservative fallback is tested separately')
        self.assertFalse(path.is_symlink(), 'Manifest must not be a symlink')
        data = impact.validate_manifest(json.loads(path.read_text(), object_pairs_hook=impact.unique_object))
        impact.ci_selection(impact.affected(data, ['AGENTS.md']))


class GitImpactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.run_git('init', '-b', 'main')
        self.run_git('config', 'user.email', 'test@example.invalid')
        self.run_git('config', 'user.name', 'Test')
        self.write(impact.MANIFEST, json.dumps(manifest()))
        for name in ['api', 'web', 'worker']:
            self.write(name + '/code.txt', 'initial\n')
        self.base = self.save()

    def run_git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def write(self, path, text):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def save(self):
        self.run_git('add', '-A')
        self.run_git('commit', '-m', 'fixture')
        return self.run_git('rev-parse', 'HEAD')

    def diverge(self, pr_path='web/code.txt', base_path='worker/code.txt'):
        self.run_git('checkout', '-b', 'issue', self.base)
        self.write(pr_path, 'issue change\n')
        head = self.save()
        self.run_git('checkout', 'main')
        self.write(base_path, 'main change\n')
        return head, self.save()

    def report(self, head, new_base):
        return impact.drift(self.repo, self.base, new_base, head, 'python=3.11;linux;fixture-v1')

    def test_independent_base_advance_preserves_inputs_without_rewriting_head(self):
        head, new_base = self.diverge()
        before = self.run_git('show-ref')
        result = self.report(head, new_base)
        self.assertTrue(result['reuse_eligible'])
        self.assertEqual(result['components'], ['web'])
        self.assertNotEqual(result['old_tree'], result['new_tree'])
        self.assertEqual(self.run_git('show-ref'), before)
        self.assertEqual(self.run_git('status', '--porcelain'), '')
        self.assertEqual(result['head'], head)

    def test_changed_dependency_invalidates_even_without_text_conflicts(self):
        head, new_base = self.diverge(base_path='api/code.txt')
        result = self.report(head, new_base)
        self.assertFalse(result['reuse_eligible'])
        self.assertIn('web', result['overlap'])

    def test_common_downstream_consumer_prevents_false_independence(self):
        data = manifest()
        data['components']['acceptance'] = spec(['acceptance/'], ['api', 'worker'], ['epics'])
        self.write(impact.MANIFEST, json.dumps(data)); self.base = self.save()
        head, new_base = self.diverge(pr_path='api/code.txt')
        result = self.report(head, new_base)
        self.assertFalse(result['reuse_eligible'])
        self.assertIn('acceptance', result['overlap'])

    def test_conflicting_merge_is_not_equivalent(self):
        head, new_base = self.diverge(base_path='web/code.txt')
        with self.assertRaisesRegex(impact.ImpactError, 'merge conflicts'):
            self.report(head, new_base)

    def test_manifest_change_cannot_exempt_its_own_candidate(self):
        head, _ = self.diverge()
        data = manifest(); data['components']['web']['depends_on'] = []
        self.write(impact.MANIFEST, json.dumps(data))
        new_base = self.save()
        self.assertFalse(self.report(head, new_base)['reuse_eligible'])
        plan = impact.plan(self.repo, self.base, new_base)
        self.assertTrue(plan['full'])
        self.assertIn('profiles', plan['checks'])

    def test_pr_manifest_change_and_unknown_base_file_are_conservative(self):
        for path in [impact.MANIFEST, 'new-area/file']:
            with self.subTest(path=path):
                head, new_base = self.diverge(base_path=path)
                self.assertFalse(self.report(head, new_base)['reuse_eligible'])
                self.run_git('checkout', 'main')
                self.run_git('branch', '-D', 'issue')
                self.run_git('reset', '--hard', self.base)

    def test_rewritten_base_history_is_not_forward_drift(self):
        head, _ = self.diverge()
        self.assertFalse(impact.drift(self.repo, head, self.base, head, 'env')['reuse_eligible'])

    def test_renames_deletions_and_newline_paths_are_complete(self):
        self.run_git('mv', 'api/code.txt', 'worker/renamed.txt')
        self.write('web/file\nwith-newline.txt', 'x')
        head = self.save()
        result = impact.plan(self.repo, self.base, head)
        self.assertEqual(set(result['changed_paths']),
                         {'api/code.txt', 'worker/renamed.txt', 'web/file\nwith-newline.txt'})
        self.assertEqual(result['components'], ['api', 'web', 'worker'])

    def test_diff_does_not_have_the_hosted_path_filter_file_limit(self):
        for i in range(350):
            self.write(f'worker/file-{i}', 'x')
        self.write('api/last-file', 'x')
        result = impact.plan(self.repo, self.base, self.save())
        self.assertEqual(len(result['changed_paths']), 351)
        self.assertEqual(result['components'], ['api', 'web', 'worker'])

    def test_missing_manifest_falls_back_but_bad_manifest_fails(self):
        self.run_git('rm', impact.MANIFEST)
        without = self.save()
        self.assertTrue(impact.plan(self.repo, without, without)['full'])
        self.write(impact.MANIFEST, '{bad json')
        bad = self.save()
        with self.assertRaises(impact.ImpactError):
            impact.plan(self.repo, bad, bad)

    def test_fingerprint_tracks_dependencies_environment_modes_and_not_commit_id(self):
        data = manifest()
        before = impact.fingerprint(self.repo, self.base, data, 'web', 'env')
        self.write('worker/code.txt', 'independent')
        unrelated = self.save()
        self.assertEqual(before, impact.fingerprint(self.repo, unrelated, data, 'web', 'env'))
        self.assertNotEqual(before, impact.fingerprint(self.repo, unrelated, data, 'web', 'other-env'))
        self.run_git('update-index', '--chmod=+x', 'api/code.txt')
        self.run_git('commit', '-m', 'mode')
        mode = self.run_git('rev-parse', 'HEAD')
        self.assertNotEqual(before, impact.fingerprint(self.repo, mode, data, 'web', 'env'))

    def test_custom_merge_drivers_cannot_execute_during_equivalence_analysis(self):
        head, new_base = self.diverge()
        self.run_git('config', 'merge.external.driver', 'false')
        with self.assertRaisesRegex(impact.ImpactError, 'Custom merge drivers'):
            self.report(head, new_base)

    def test_real_ci_payload_uses_accepted_policy_not_candidate_exemptions(self):
        root = Path(__file__).resolve().parents[2]
        workflow = (root / '.github/workflows/executor-routing-ci.yml').read_text()
        payload = textwrap.dedent(workflow.split("python3 - <<'PY'\n", 1)[1]
                                  .split('          PY', 1)[0])

        def execute(base, head):
            with tempfile.TemporaryDirectory() as output_dir:
                output = Path(output_dir) / 'outputs'
                env = {**os.environ, 'BASE_SHA': base, 'TEST_SHA': head,
                       'GITHUB_OUTPUT': str(output)}
                completed = subprocess.run([sys.executable, '-c', payload], cwd=self.repo,
                                           env=env, capture_output=True, text=True)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                values = dict(line.split('=', 1) for line in output.read_text().splitlines())
                (self.repo / 'component-plan.json').unlink()
                return {key for key, value in values.items() if value == 'true'}

        self.assertEqual(execute(self.base, self.base), set(impact.CI_CHECKS))
        self.write('.github/scripts/component_impact.py', (root / '.github/scripts/component_impact.py').read_text())
        trusted_base = self.save()
        self.write('worker/code.txt', 'changed')
        head = self.save()
        self.assertEqual(execute(trusted_base, head), {'cleanup', 'components'})
        self.write('.github/scripts/component_impact.py', "raise SystemExit('untrusted policy executed')\n")
        data = manifest(); data['components']['worker']['checks'] = []
        self.write(impact.MANIFEST, json.dumps(data))
        self.assertEqual(execute(trusted_base, self.save()), set(impact.CI_CHECKS))

    def test_missing_object_and_moving_refs_never_return_a_green_plan(self):
        for ref in ['main', 'f' * 40, '--help']:
            with self.subTest(ref=ref), self.assertRaises(impact.ImpactError):
                impact.plan(self.repo, ref, self.base)


if __name__ == '__main__':
    unittest.main()
