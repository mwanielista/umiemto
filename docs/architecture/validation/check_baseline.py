#!/usr/bin/env python3
"""Validate baseline architecture artifacts, not application implementation."""

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


ARCHITECTURE = Path(__file__).resolve().parents[1]
REPOSITORY = ARCHITECTURE.parents[1]
ADR_SECTIONS = (
    'Status', 'Context', 'Problem', 'Constraints', 'Considered options',
    'Decision', 'Rationale', 'Consequences', 'Risks', 'Rejected alternatives',
    'Validation / fitness functions',
)
ADR_STATUSES = {'Proposed', 'Accepted', 'Deprecated', 'Superseded'}


def validate_model(model):
    errors = []
    if model.get('schemaVersion') != 1 or model.get('state') != 'target':
        errors.append('Model must have schemaVersion 1 and explicitly target state')
    if model.get('rootPackage') != 'pl.eszkola' or model.get('publicContractPackage') != 'api':
        errors.append('Unexpected package boundary convention')
    modules = model.get('modules', [])
    if not isinstance(modules, list) or not modules:
        return errors + ['Nonempty modules array required']
    names = [module['id'] for module in modules]
    if len(set(names)) != len(names):
        errors.append('Duplicate module ID')
    graph = {}
    owners = {}
    for module in modules:
        name = module['id']
        if not re.fullmatch(r'[a-z]+', name):
            errors.append(f'Invalid module ID: {name}')
        dependencies = module['allowedDependencies']
        if len(set(dependencies)) != len(dependencies):
            errors.append(f'Duplicate dependency in {name}')
        for dependency in dependencies:
            if dependency not in names:
                errors.append(f'Unknown dependency: {name} -> {dependency}')
            if dependency == name:
                errors.append(f'Self dependency: {name}')
        graph[name] = dependencies
        if name == 'workflows' and module['ownedEntities']:
            errors.append('Workflows must not own business entities')
        for entity in module['ownedEntities']:
            if entity in owners:
                errors.append(f'Duplicate entity owner: {entity}')
            owners[entity] = name
    for entity in ('ModuleDefinition', 'ProgramVersion', 'ScheduledGroup', 'LessonOccurrence', 'Enrollment'):
        if entity not in owners:
            errors.append(f'Missing distinct delivery concept: {entity}')
    active, complete = set(), set()

    def visit(name):
        if name in active:
            errors.append(f'Dependency cycle at {name}')
            return
        if name in complete or name not in graph:
            return
        active.add(name)
        for dependency in graph[name]:
            visit(dependency)
        active.remove(name)
        complete.add(name)

    for name in graph:
        visit(name)
    return errors


def validate_documents(model):
    errors = []
    files = list(ARCHITECTURE.rglob('*.md')) + list((REPOSITORY / 'docs/requirements').rglob('*.md'))
    for path in files:
        content = path.read_text()
        for destination in re.findall(r'\[[^\]]*\]\(([^\s)]+)\)', content):
            target = destination.split('#', 1)[0]
            if not target or re.match(r'^[a-z]+:', target):
                continue
            if not (path.parent / unquote(target)).exists():
                errors.append(f'Missing link in {path.relative_to(REPOSITORY)}: {target}')
    adrs = sorted((ARCHITECTURE / 'decisions').glob('*.md'))
    if not adrs:
        errors.append('No ADRs found')
    for path in adrs:
        content = path.read_text()
        if not content.startswith('# ADR-'):
            errors.append(f'Missing ADR title: {path.name}')
        headings = set(re.findall(r'^## (.+)$', content, re.MULTILINE))
        for heading in ADR_SECTIONS:
            if heading not in headings:
                errors.append(f'{path.name}: missing section {heading}')
        status = re.search(r'^## Status\s+([A-Za-z]+)', content, re.MULTILINE)
        if not status or status.group(1) not in ADR_STATUSES:
            errors.append(f'{path.name}: invalid status')
    ownership = (ARCHITECTURE / 'data-model.md').read_text()
    for module in model['modules']:
        row = re.search(r'^\| ' + module['id'] + r' \| (.+) \|$', ownership, re.MULTILINE)
        if not row:
            errors.append(f'Missing ownership row for {module["id"]}')
        elif module['ownedEntities'] != []:
            documented = [item.strip() for item in row.group(1).split(',')]
            if set(documented) != set(module['ownedEntities']):
                errors.append(f'Ownership table differs from model: {module["id"]}')
    return errors


def self_test(model):
    tests = []
    duplicate_module = copy.deepcopy(model)
    duplicate_module['modules'].append(copy.deepcopy(duplicate_module['modules'][0]))
    tests.append(('duplicate module', duplicate_module, 'Duplicate module ID'))
    duplicate_owner = copy.deepcopy(model)
    duplicate_owner['modules'][1]['ownedEntities'].append('AuditEvent')
    tests.append(('duplicate owner', duplicate_owner, 'Duplicate entity owner'))
    unknown = copy.deepcopy(model)
    unknown['modules'][0]['allowedDependencies'].append('missing')
    tests.append(('unknown dependency', unknown, 'Unknown dependency'))
    cyclic = copy.deepcopy(model)
    cyclic['modules'][0]['allowedDependencies'].append('identity')
    tests.append(('cycle', cyclic, 'Dependency cycle'))
    self_edge = copy.deepcopy(model)
    self_edge['modules'][0]['allowedDependencies'].append('audit')
    tests.append(('self dependency', self_edge, 'Self dependency'))
    workflow_data = copy.deepcopy(model)
    workflow_data['modules'][-1]['ownedEntities'].append('WorkflowOrder')
    tests.append(('workflow ownership', workflow_data, 'Workflows must not own'))
    failures = []
    for name, candidate, expected in tests:
        if not any(expected in error for error in validate_model(candidate)):
            failures.append(f'Self-test failed to reject {name}')
    return failures, len(tests)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    try:
        model = json.loads((ARCHITECTURE / 'model.json').read_text())
        errors = validate_model(model) + validate_documents(model)
        count = 0
        if args.self_test:
            failures, count = self_test(model)
            errors.extend(failures)
    except (OSError, ValueError, KeyError, TypeError) as error:
        errors = [f'Invalid baseline artifact: {error}']
    if errors:
        for error in errors:
            print(f'FAIL: {error}', file=sys.stderr)
        return 1
    print(f'PASS: target model, {len(model["modules"])} modules, unique ownership, DAG, ADRs and local links')
    if args.self_test:
        print(f'PASS: {count} invalid model cases rejected')
    return 0


if __name__ == '__main__':
    sys.exit(main())
