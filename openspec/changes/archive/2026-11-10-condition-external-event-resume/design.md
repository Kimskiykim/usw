# Design

## Context

Мотивация и границы — [proposal](proposal.md). Рецепт сейчас обещает resume
в строках 11–13, не называя условия handoff. Нормы:
`live-operation-state` § «Отключённая capability не касается HANDOFF»;
run `SKILL.md`:85–88 задаёт только ephemeral identity при `false`.
Применены architecture invariants 1/2/6 и ADR-001: текстовая подсказка не
создаёт durable runtime или курсор.

## Goals / Non-Goals

Решение касается содержания предлагаемого автором блока. Полный DoD/proof,
production/test/norm paths и follow-up находятся только в
[leaf task](tasks/1.1-honest-wait-continuation/task.md).

## Decisions

1. **Два способа повторного входа в одном рецепте.** Сохранить один read-only
   check и `blocked`; условие handoff оформить понятной прозой вокруг примера.
   При `false` передавать контекст в ответе для ручного переноса. Вариант
   «всегда вызвать Resume» отвергнут: конфигурация запрещает state access.
   Вариант обязательного файла checkpoint отвергнут: это новый протокол.
2. **Норма в existing `guided-flow-authoring`.** Добавляется требование к
   authoring guidance; `live-operation-state` остаётся источником recovery
   semantics. Main spec `flow-design-patterns` в этом baseline отсутствует:
   соседний незавершённый catalog change не становится зависимостью.
3. **Обычные роли и локальные действия.** Исходный independent reader без
   planning/card подсказок воспроизвёл обещание, затем сверил disabled norms.
   Actual `resume` в `/tmp` вернул `handoff_disabled`, exit 2, sentinel state
   и counter=1 неизменны. Это ограниченный proof дефекта, не успешное
   cross-session исполнение. Planning evidence:
   `.usw/state/create-flow-improvement/condition-external-event-resume/`:
   `ordinary-reader-relay.md` (relay excerpt), `disabled-resume-action.json`
   (actual command/bytes), `baseline.json`. Future proof — в leaf.
4. **Независимая копия и identities.** Рабочий root:
   `/Users/leonidkim/.codex/parallel-workspaces/usw/20261110-92635ffc/create-flow`,
   branch `codex/usw-create-flow-improvement`, baseline HEAD
   `2cee3137e6ed637a7ab94558f637fc1259014b9d`, product source
   `usw-source-v1:908b2a81bc2a05a9413396a2319639fe3af91542a6d4939c7b211634b54e0a90`.
   T01 не включён, installed T01 не используется. CLI подтвердил root и
   `spec-driven`; `artifacts.root=openspec/changes`, `flows.root=usw/flows`,
   `reviews.root=usw/reviews`. Legacy `refinement.root=usw/refinements`
   не является active v1 field (контракт `workspace-configuration`).
   Source exclusions: только `.git`, `.usw`, `openspec/changes`,
   `usw/flows`, `usw/reviews`; legacy `usw/refinements` входит в source.
   Leaf revision `i13-wait-c1`; stable digest исключает anchored
   `## Milestone log` по существующему artifact contract helper.
   Все 6 raw planning hashes и stable digest отдельно фиксируются в local
   `planning-identities-v2.json`; без self-reference в planning artifacts.
5. **Передача writer права.** Planning writer меняет только этот change и
   local evidence; один `[ ]` остаётся в `tasks.md`. Independent critic
   получает шесть точных artifacts; назначенный planning receipt path:
   `usw/reviews/change/condition-external-event-resume/i13-wait-c1-planning-critic.md`
   (ещё не создан, принадлежит critic). Development/Testing evidence — соответственно
   `tasks/1.1-honest-wait-continuation/development-evidence.md` и
   `testing-evidence.md`, пока не создаются. Task review path:
   `usw/reviews/task/condition-external-event-resume/1.1/i13-wait-c1-internal-testing.md`
   (назначенный путь будущего receipt; ещё не создан).
   Writer release/Delivery pointer — local `delivery-v2.md`; review/apply
   остаются отдельными назначениями.

## Risks / Trade-offs

- Независимый читатель может обобщить promise → проверить его actual preview
  и действия по двум режимам, не засчитывать наличие слова как поведение.
- Ручной context теряется между сессиями → честно передать его человеку;
  не обещать сохранение платформой или новый recovery destination.
- AUD-I13 составной → после apply отметить только wait subitem, сохранить
  `backlog` и явный остаток двух других частей.
- Около 1000+ connected changed lines требуют отдельного согласия по
  GIGACODE; текущая оценка planning+apply 400–600, предел без него не пересекать.

## Migration Plan

Planning не мигрирует состояние, не устанавливает пакет и не интегрирует
копию. После отдельного apply включить main-spec/card/index edits в конечный
manifest до всех обязательных checks и независимой приёмки. Установка/новая
сессия/интеграция назначаются отдельно; global installation writer не трогает.
