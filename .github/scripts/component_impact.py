"""Conservative component impact and Git input-equivalence reports (no mutations).

See docs/component-isolation.md. Reports select validation; they never grant merge
permission or turn an old/failed CI result into a successful check.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

MANIFEST = '.skillforge/components.json'
GLOBAL = (MANIFEST, 'AGENTS.md', '.github/workflows/',
          '.github/scripts/component_impact.py',
          '.github/scripts/test_component_impact.py', 'docs/component-isolation.md')
CI_CHECKS = ('routing', 'profiles', 'cleanup', 'epics', 'template', 'components')
IDENTIFIER = re.compile(r'[a-z][a-z0-9_-]*\Z')
SHA = re.compile(r'[0-9a-f]{40}\Z')


class ImpactError(ValueError):
    """Incomplete or ambiguous evidence must not authorize selective validation."""


def git(repo: Path, *args: str, allowed=(0,)) -> subprocess.CompletedProcess:
    result = subprocess.run(['git', '--no-replace-objects', '-C', str(repo), *args], capture_output=True)
    if result.returncode not in allowed:
        raise ImpactError(f'git {args[0]} failed: ' +
                          result.stderr.decode('utf-8', 'replace').strip())
    return result


def commit(repo: Path, revision: str) -> str:
    if not SHA.fullmatch(revision):
        raise ImpactError('Use an exact, lowercase 40-hex commit SHA, not a moving ref')
    if git(repo, 'cat-file', '-t', revision).stdout.strip() != b'commit':
        raise ImpactError('Expected a commit object')
    return revision


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ImpactError(f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def strings(value, label: str, nonempty=False):
    if (not isinstance(value, list) or (nonempty and not value)
            or any(not isinstance(x, str) or not x for x in value)
            or len(set(value)) != len(value)):
        raise ImpactError(f'{label} must be a list of unique nonempty strings')
    return value


def validate_manifest(data):
    if not isinstance(data, dict) or set(data) - {'version', 'components', 'global_paths'}:
        raise ImpactError('Unknown manifest fields')
    if type(data.get('version')) is not int or data['version'] != 1:
        raise ImpactError('Unsupported manifest version')
    components = data.get('components')
    if not isinstance(components, dict) or not components:
        raise ImpactError('At least one component is required')
    paths = list(strings(data.get('global_paths', []), 'global_paths'))
    for name, spec in components.items():
        if not IDENTIFIER.fullmatch(name) or not isinstance(spec, dict):
            raise ImpactError('Invalid component identifier or definition')
        if set(spec) != {'paths', 'depends_on', 'checks'}:
            raise ImpactError(f'{name}: expected paths, depends_on and checks')
        paths += strings(spec['paths'], f'{name}.paths', nonempty=True)
        for dependency in strings(spec['depends_on'], f'{name}.depends_on'):
            if dependency not in components or dependency == name:
                raise ImpactError(f'{name}: unknown or self dependency')
        for check in strings(spec['checks'], f'{name}.checks'):
            if not IDENTIFIER.fullmatch(check):
                raise ImpactError('Invalid check identifier')
    for path in paths:
        if (path.startswith('/') or any(c in path for c in '\\*?[]\x00\n\r')
                or any(part in ('', '.', '..') for part in path.rstrip('/').split('/'))):
            raise ImpactError('Paths must be exact relative files or directory prefixes ending /')
    pending = set(components)
    while pending:
        ready = {name for name in pending
                 if not (set(components[name]['depends_on']) & pending)}
        if not ready:
            raise ImpactError('Component dependency cycle')
        pending -= ready
    return data


def manifest_at(repo: Path, revision: str):
    entry = git(repo, 'ls-tree', '-z', revision, '--', MANIFEST).stdout
    if not entry:
        return None
    if not entry.startswith((b'100644 blob ', b'100755 blob ')):
        raise ImpactError('Manifest must be an ordinary tracked JSON file')
    try:
        raw = git(repo, 'show', f'{revision}:{MANIFEST}').stdout.decode('utf-8')
        return validate_manifest(json.loads(raw, object_pairs_hook=unique_object))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ImpactError('Invalid manifest JSON') from exc


def matches(path: str, patterns) -> bool:
    return any(path.startswith(p) if p.endswith('/') else path == p for p in patterns)


def owners(data, path: str) -> set[str]:
    return {name for name, spec in data['components'].items() if matches(path, spec['paths'])}


def closure(data, selected: set[str], *, reverse: bool) -> set[str]:
    selected = set(selected)
    while True:
        expanded = set(selected)
        for name, spec in data['components'].items():
            if reverse and set(spec['depends_on']) & selected:
                expanded.add(name)
            elif not reverse and name in selected:
                expanded.update(spec['depends_on'])
        if expanded == selected:
            return selected
        selected = expanded


def affected(data, paths) -> dict:
    paths = sorted(set(paths))
    if data is None:
        return {'full': True, 'reason': 'no-manifest', 'components': [], 'checks': []}
    direct, reason = set(), None
    for path in paths:
        found = owners(data, path)
        if matches(path, (*GLOBAL, *data.get('global_paths', []))):
            reason = 'global-input'
        elif not found and reason is None:
            reason = 'unmapped-path'
        direct.update(found)
    selected = set(data['components']) if reason else closure(data, direct, reverse=True)
    checks = {check for name in selected for check in data['components'][name]['checks']}
    return {'full': reason is not None, 'reason': reason or 'component-closure',
            'components': sorted(selected), 'checks': sorted(checks)}


def ci_selection(report: dict) -> dict[str, bool]:
    """Canonical template check registry; unknown checks cannot be silently skipped."""
    if not isinstance(report, dict) or type(report.get('full')) is not bool:
        raise ImpactError('Invalid CI plan')
    requested = strings(report.get('checks', []), 'checks')
    if set(requested) - set(CI_CHECKS):
        raise ImpactError('Plan names a check absent from the CI registry')
    return {name: report['full'] or name == 'components' or name in requested
            for name in CI_CHECKS}



def changed(repo: Path, before: str, after: str) -> list[str]:
    # No path pagination/truncation; renames include both the deleted and added path.
    raw = git(repo, 'diff', '--no-ext-diff', '--no-renames', '--name-only', '-z',
              before, after, '--').stdout
    return [p.decode('utf-8', 'surrogateescape') for p in raw.split(b'\0') if p]


def plan(repo: Path, base: str, head: str) -> dict:
    commit(repo, base)
    commit(repo, head)
    paths = changed(repo, base, head)
    return {'base': base, 'head': head, 'changed_paths': paths,
            **affected(manifest_at(repo, base), paths)}


def fingerprint(repo: Path, revision: str, data, component: str, environment: str) -> str:
    if data is None or component not in data['components'] or not environment.strip():
        raise ImpactError('Fingerprint requires a known component and an explicit environment key')
    domain = closure(data, {component}, reverse=False)
    inputs = []
    for entry in git(repo, 'ls-tree', '-r', '-z', revision).stdout.split(b'\0'):
        if not entry:
            continue
        metadata, raw_path = entry.split(b'\t', 1)
        path = raw_path.decode('utf-8', 'surrogateescape')
        found = owners(data, path)
        if not found or found & domain or matches(path, (*GLOBAL, *data.get('global_paths', []))):
            inputs.append([path, metadata.decode('ascii')])
    payload = [1, component, environment, data, sorted(inputs)]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode('ascii')).hexdigest()


def merge_tree(repo: Path, base: str, head: str) -> str:
    if git(repo, 'config', '--get-regexp', r'^merge\..*\.driver$', allowed=(0, 1)).stdout:
        raise ImpactError('Custom merge drivers require conservative integration')
    result = git(repo, 'merge-tree', '--write-tree', base, head, allowed=(0, 1))
    if result.returncode:
        raise ImpactError('Candidate has Git merge conflicts')
    tree = result.stdout.splitlines()[0].decode('ascii')
    if not SHA.fullmatch(tree):
        raise ImpactError('Missing exact candidate tree')
    return tree


def drift(repo: Path, old_base: str, new_base: str, head: str, environment: str) -> dict:
    for revision in (old_base, new_base, head):
        commit(repo, revision)
    result = {'old_base': old_base, 'new_base': new_base, 'head': head,
              'reuse_eligible': False, 'environment_key': environment}
    if git(repo, 'merge-base', '--is-ancestor', old_base, new_base, allowed=(0, 1)).returncode:
        return {**result, 'reason': 'base-history-rewritten'}
    common = git(repo, 'merge-base', '--all', old_base, head).stdout.splitlines()
    if len(common) != 1:
        raise ImpactError('Require exactly one PR merge base')
    data = manifest_at(repo, old_base)
    pr = affected(data, changed(repo, common[0].decode('ascii'), head))
    advance = affected(data, changed(repo, old_base, new_base))
    if pr['full'] or advance['full'] or not pr['components']:
        return {**result, 'reason': 'global-unmapped-or-missing-scope', 'pr': pr, 'advance': advance}
    old_tree, new_tree = merge_tree(repo, old_base, head), merge_tree(repo, new_base, head)
    actual = affected(data, changed(repo, old_tree, new_tree))
    overlap = sorted(set(pr['components']) & (set(advance['components']) | set(actual['components'])))
    if actual['full'] or overlap:
        return {**result, 'reason': 'affected-domain-overlap', 'overlap': overlap}
    fingerprints = {}
    for name in pr['components']:
        before = fingerprint(repo, old_tree, data, name, environment)
        after = fingerprint(repo, new_tree, data, name, environment)
        if before != after:
            return {**result, 'reason': 'input-fingerprint-changed', 'component': name}
        fingerprints[name] = after
    return {**result, 'reuse_eligible': True, 'reason': 'independent-forward-drift',
            'old_tree': old_tree, 'new_tree': new_tree, 'components': pr['components'],
            'fingerprints': fingerprints}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path('.'))
    commands = parser.add_subparsers(dest='command', required=True)
    command = commands.add_parser('plan')
    command.add_argument('--base', required=True)
    command.add_argument('--head', required=True)
    command = commands.add_parser('drift')
    for name in ('old-base', 'new-base', 'head', 'environment-key'):
        command.add_argument('--' + name, required=True)
    command = commands.add_parser('fingerprint')
    for name in ('revision', 'component', 'environment-key'):
        command.add_argument('--' + name, required=True)
    command = commands.add_parser('validate')
    command.add_argument('--revision', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'plan':
            result = plan(args.repo, args.base, args.head)
        elif args.command == 'drift':
            result = drift(args.repo, args.old_base, args.new_base, args.head, args.environment_key)
        else:
            commit(args.repo, args.revision)
            data = manifest_at(args.repo, args.revision)
            result = ({'manifest_present': data is not None} if args.command == 'validate' else
                      {'fingerprint': fingerprint(args.repo, args.revision, data,
                                                  args.component, args.environment_key)})
        print(json.dumps(result, sort_keys=True))
        return 0
    except (ImpactError, OSError) as exc:
        print(json.dumps({'full': True, 'reuse_eligible': False, 'error': str(exc)}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
