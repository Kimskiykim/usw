## Context

Flow версии `1` уже разбирается детерминированно и выполняется по одному шагу.
`version-2` пока является creation-only prose-first контрактом: он вводит
постоянные имена, typed calls, decisions, bounded loops, parallel blocks и
вложенный subagent payload, но сознательно не определяет runtime state.

Runtime не может безопасно угадывать смысл произвольной фразы. Поэтому change
фиксирует executable-поднабор уже существующей канонической формы и сохраняет
остальной Markdown только как документацию.

## Goals / Non-Goals

**Goals:**

- детерминированно валидировать и исполнять канонический `version-2`;
- поддержать все объявленные `CALL` types и управляющие маркеры;
- сохранить одну observable orchestration boundary за invocation;
- разрешать все executors до первого side effect;
- возобновлять branch/loop state без нового state-файла;
- полностью сохранить parsing и runtime версии `1`.

**Non-Goals:**

- интерпретировать произвольный prose как программу во время запуска;
- добавлять `MODEL`, неограниченные loops или произвольные jumps;
- автоматически доказывать независимость parallel children;
- добавлять dependency либо отдельный scheduler/service;
- предоставлять внешние полномочия на commit, push, deploy или release.

## Decisions

### 1. Runner принимает только канонический executable-поднабор

Parser выбирается по точному значению версии. Для `version-2` он требует
последовательные верхнеуровневые номера, глобально уникальные kebab-case имена,
точные uppercase `CALL` types и канонические строки управляющих маркеров.
Неизвестная либо двусмысленная форма отклоняется с line-aware ошибкой до
разрешения executors.

Отдельный machine manifest отклонён: он создал бы второй источник истины.
Свободная LLM-интерпретация отклонена на runtime boundary как
недетерминированная.

### 2. Typed call передаётся executor как явный invocation

`SKILL` сохраняет существующий exact-name registry, а `HUMAN`, `SUBAGENT` и
`FLOW` разрешаются по паре `(kind, target)`. Invocation содержит kind, target,
scope, literal arguments и вложенный payload. `SCRIPT` остаётся внутренним
безопасным adapter без shell.

Это позволяет субагенту получить принадлежащие ему nested actions, а flow и
human adapters подключить без знания о них в parser. Универсальный string
command отклонён, потому что потерял бы type и вернул shell-like ambiguity.

### 3. Управляющее состояние остаётся малым и явным

Gate outcome выбирает exact target из полного `IF`/`ELIF` набора; `ELSE`
останавливает запуск с `decision_required` для неизвестного результата.
Loop хранит счётчик завершённых попыток, после каждой попытки возвращается к
объявленному gate и при повторном входе после лимита останавливается как
`loop_exhausted`.

Текущий action index и loop counters входят в существующий cursor/checkpoint
contract. Для v2 checkpoint получает schema version 2, а reader продолжает
принимать v1. Новый state-файл не создаётся; production protocol по-прежнему
фиксирует boundary через HANDOFF.

### 4. PARALLEL является одной orchestration boundary

Перед стартом runner разрешает всех children. Затем он вызывает children
concurrently, ждёт всех результатов и агрегирует writes/references в порядке
документа. Любой non-completed child останавливает block; следующий
верхнеуровневый пункт не становится доступным.

Последовательная имитация отклонена, потому что меняет явно запрошенную
семантику. Отдельный постоянный scheduler отклонён как лишняя инфраструктура;
достаточен стандартный bounded thread pool на число children.

### 5. Composite calls остаются executor boundaries

`CALL SUBAGENT` и `CALL FLOW` являются одним вызовом родительского flow.
Subagent adapter обязан выполнить переданный nested payload; flow adapter —
названный child flow. Они возвращают общий structured outcome и не продвигают
родительский cursor до полного `completed`.

Так родитель не смешивает своё состояние с внутренним состоянием composite
executor. Автоматическое разворачивание child flow в parent graph отклонено:
оно требует cursor stack и меняет identity родительского контракта.

## Risks / Trade-offs

- [Существующий prose-first документ может не попасть в executable-поднабор] →
  обновить canonical reference и возвращать точную validation error до запуска.
- [Parallel children могут фактически конфликтовать] → creator обязан выводить
  `PARALLEL` только для явно независимой работы; runner preflight проверяет все
  executors, но не обещает доказательство независимости.
- [Composite executor скрывает внутренние шаги от parent cursor] → payload и
  target входят в invocation, а outcome/references агрегируются на boundary.
- [Loop outcome не входит в объявленный gate] → `ELSE` требует решения и не
  допускает неявного перехода.

## Migration Plan

1. Добавить v2 data model/parser, не меняя ветку v1.
2. Добавить typed executor adapters и control-flow state.
3. Расширить validation report, skill contract и canonical reference.
4. Добавить focused tests для всех CALL/control types и полную регрессию.

Откат удаляет v2 parser/runtime branch. Flow версии `1` и созданные
`version-2` документы остаются без миграции, но снова становятся creation-only.

## Open Questions

Нет блокирующих вопросов.
