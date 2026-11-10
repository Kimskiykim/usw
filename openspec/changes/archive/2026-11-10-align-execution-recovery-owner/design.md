# Design

## Context

Мотивация — [proposal.md](proposal.md). Статическое evidence AUD-T08 остаётся
применимым: `execution-artifacts:14–26`, `62–70`, `173–190` конфликтуют с
`live-operation-state:9–17`, `49–53`. Фактическая порча router не утверждается.

Baseline копии: branch `codex/usw-run-handoff-improvement`,
HEAD `2cee3137e6ed637a7ab94558f637fc1259014b9d`,
`usw-source-v1:908b2a81bc2a05a9413396a2319639fe3af91542a6d4939c7b211634b54e0a90`.
Это принятый F05 baseline без T01; установленный пакет и root checkout не
являются source этой ветки. Сверка F04: manage Show/Resume уже ждёт явного
продолжения той же операции, требует freshness/reason для повторной проверки;
run различает `blocked` и `decision_required`. Переданное наблюдение обычного
reader на root не переименовывается в новый proof ветки. F04 здесь не меняется.

Инварианты — `openspec/context/03-architecture.md`, ADR-001: root владеет
своим state, текст не даёт полномочий, нового runtime нет. Дизайн нужен для
явного разрешения нормативного конфликта по критерию существующей AUD-T08.

## Goals / Non-Goals

**Goals:** один recovery owner с сохранением самостоятельной роли shared
artifacts. Полный DoD и проверка находятся только в leaf task.

**Non-Goals:** менять authoritative routed contract ради старого single-state
места записи, добавлять историю tools, machine plan или новый artifact.

## Decisions

### 1. Исправить три существующих requirement blocks

Delta сохраняет полные blocks «Один владелец…», «Generic handoff…»,
«Replanning…» и все пять их scenarios. Меняется только назначение recovery
content: ссылка на `live-operation-state` и exact operation document;
HANDOFF — router. Pending действия не означают новые routed operations.

Альтернатива считать всю `execution-artifacts` исторической отвергнута:
актуальные completion, contracts, evidence, freshness и receipts остаются
нормативными. Переопределение routed backend также не решает этот конфликт
узко. `live-operation-state`, SKILL и backend уже согласованы между собой;
их правка создала бы лишний scope.

### 2. Закрепить разделение обязанностей адресным тестом

В будущем `tests/test_execution_recovery_contract.py` читает requirement и
scenario blocks main specs: owner для pause/replanning — operation document,
router не является narrative state. Фиксируются path/role/contract anchors,
а не целые русские предложения. Сохранность task/evidence/review норм
проверяется сравнением незатронутых blocks и scenarios с baseline при review.
Это contract-test нормативных текстов; новое backend-воспроизведение Resume
не требуется. Независимый обычный reader получает действующие specs и задачу
определить место pause/replanning, без алгоритма автора. Он не запускает модель
через CLI/API. Детальные checks и ограничения — leaf Verification.

### 3. Использовать существующие roots и одну leaf task

Native OpenSpec root и cwd:
`/Users/leonidkim/.codex/parallel-workspaces/usw/20261110-92635ffc/run-handoff`.
Активные v1 roots `usw.yaml`: artifacts `openspec/changes`, flows `usw/flows`,
reviews `usw/reviews`. Legacy `refinement.root: usw/refinements` не активно
по `workspace-configuration` и не исключает этот путь из product manifest.
Canonical source exclusions — ровно `.git`, `.usw`, `openspec/changes`,
`usw/flows`, `usw/reviews`. `openspec list/context` до первой записи разрешили
эту копию.

Task: `openspec/changes/align-execution-recovery-owner/tasks/1.1-align-recovery-owner/task.md`.
Будущие role-owned files — `development-evidence.md` и `testing-evidence.md`
в том же task directory. Change receipts —
`usw/reviews/change/align-execution-recovery-owner/<review-id>.md`, task receipts —
`usw/reviews/task/align-execution-recovery-owner/1.1/<review-id>.md`.
Planner не создаёт role evidence или receipts. Локальные planning proof,
raw hashes и delivery pointer —
`.usw/state/run-handoff/align-execution-recovery-owner/`; append-only лог —
`.usw/state/run-handoff/decision-log.md`.

### 4. Freeze после всех включённых правок

Revision `t08-c1`; stable identity определена в leaf. Raw SHA-256 каждого
planning artifact фиксируются отдельно в local
`candidate-v2/planning-freeze.json`; опубликованный v1 сохранён как history.
Main-spec sync и правки AUD-T08/индекса входят в product source, поэтому apply
делает их до конечного manifest и обязательных checks. Источники F04 не
закрывать, goal не закрывать. Бюджет connected diff: planning около 300 строк,
product/tests/card/index менее 180; ожидается менее 600 изменённых строк.
При приближении к 1000 остановиться для отдельного согласия, F05/T01 cap не
переносить. Новая очередь не создаётся.

## Risks / Trade-offs

- Скрытая потеря норм при MODIFIED → сохранить полные blocks и сравнить
  незатронутые нормы/scenarios с baseline; не сокращать ради length warnings.
- Прочтение текста не гарантирует поведение любой LLM → отчёт ограничен
  конкретной редакцией и ordinary reader observation, без таких обещаний.
- Предварительная проверка при старом source → после любого contract/source
  изменения всё task evidence stale, полный обязательный набор повторяется.

## Migration Plan

Формат state и установка не меняются. После отдельного разрешения apply
синхронизирует delta в main spec и проходит один leaf contract. Откат — вернуть
согласованные normative/test/card/index edits; operation files не мигрируют.
