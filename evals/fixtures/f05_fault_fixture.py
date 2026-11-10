#!/usr/bin/env python3
"""Isolated F05 eval fixture around a copied, unmodified handoff backend."""
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from unittest import mock

root = Path.cwd()
fixture = root / '.f05'
script = root / 'fixture-skills/usw-manage-handoff/scripts/handoff_state.py'
spec = importlib.util.spec_from_file_location('fixture_handoff', script)
backend = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = backend
spec.loader.exec_module(backend)


def log(event):
    fixture.mkdir(exist_ok=True)
    with (fixture / 'calls.jsonl').open('a') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')


def fail(*args, **kwargs):
    raise OSError('fixture injected I/O failure')


def main():
    if sys.argv[1] == '--setup':
        mode = sys.argv[2]
        fixture.mkdir(exist_ok=True)
        (fixture / 'mode').write_text(mode)
        (root / 'usw.yaml').write_text('schema_version: 1\nhandoff: true\n')
        (root / '.usw').mkdir()
        (root / '.usw/HANDOFF.md').write_text(backend.render_readable_router())
        identity = 'usw-markdown:local:' + 'a' * 64
        path, operation = backend.begin_handoff(root, 'review', 'local', identity, 'fixture work')
        backend.outcome_handoff(root, 'paused', operation=operation, done='Предыдущее: старый факт.',
                                position='Ожидание.', next_action='Продолжить.', blocker='none')
        neighbor_path, neighbor = backend.begin_handoff(root, 'review', 'local', identity, 'neighbor')
        for op, source in ((operation, path), (neighbor, neighbor_path)):
            (root / '.usw/handoffs' / backend.operation_candidate_filename(op)).write_bytes(source.read_bytes())
        (fixture / 'operation.txt').write_text(operation + '\n')
        (fixture / 'neighbor.txt').write_text(neighbor + '\n')
        (fixture / 'effect-counter.txt').write_text('1\n')
        shutil.copytree(root / '.usw', fixture / 'before-outcome')
        args = ['outcome', str(root), 'completed', '--operation', operation, '--done',
                'Результат: проверка инвентаря завершена.', '--position', 'Работа закончена.',
                '--next-action', 'Передать результат.', '--blocker', 'none', '--check', 'Проверено 3 объекта.']
        log({'phase': 'setup', 'argv': args})
        target = '_write_operation_at' if mode == 'before-document' else '_write_readable_router_locked'
        with mock.patch.object(backend, target, side_effect=fail):
            exit_code = backend.main(args)
        if exit_code != 2:
            raise RuntimeError(f'expected injected outcome failure, got {exit_code}')
        (fixture / 'outcome-exit.txt').write_text(str(exit_code) + '\n')
        return 0
    args = sys.argv[1:]
    mode = (fixture / 'mode').read_text().strip()
    log({'phase': 'agent', 'argv': args})
    target = '_read_router_locked' if mode == 'unreadable-state' and args[0] == 'show' else '_write_readable_router_locked'
    with mock.patch.object(backend, target, side_effect=fail):
        return backend.main(args)


if __name__ == '__main__':
    raise SystemExit(main())
