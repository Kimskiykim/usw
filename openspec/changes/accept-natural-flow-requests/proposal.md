# Proposal

## Why

Принятый UX допускает прямую просьбу найти или оценить flow обычными словами,
но descriptions и native metadata пока требуют вызова по имени skill.

## What Changes

- Прямая просьба о поиске или оценке именно flow активирует соответствующий
  skill без обязательного имени skill или slash-команды.
- Простое упоминание flow и общая проверка кода не активируют finder/assessor;
  неоднозначный объект требует уточнения до чтения flow.
- Native metadata разрешает выбор find/assess хостом; проверка намерения и
  read-only границы сохраняются в инструкциях.
- Общая матрица показывает способы активации и полномочия шести skills.

## Scope

AUD-I07: find/assess, их metadata, README, адресные тесты и eval scenarios.
Принятая ранее политика ручного handoff сохраняется.

## Non-goals

Автоматическое выполнение или изменение найденного flow, новый parser
естественного языка, изменение loader/runtime, установка глобальных skills.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

- `flow-discovery`: прямая обычная просьба считается явным запросом поиска.
- `flow-assessment`: прямая обычная просьба считается явным запросом оценки;
  при неоднозначном объекте требуется уточнение.

## Impact

Два SKILL.md и openai.yaml, README, package tests и behavior scenarios.
Публичные команды и read-only resolver/inspect остаются совместимыми.
