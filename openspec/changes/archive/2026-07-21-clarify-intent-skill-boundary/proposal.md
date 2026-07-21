## Why

`usw-refine-task` сейчас связывает диалоговое уточнение с task/change lifecycle
и хранит его как shared project state, хотя пользователь может формулировать
идею, проблему или решение, которое никогда не попадёт в backlog. Одновременно
flow action `clarify-intent` ошибочно разрешается в solution-brainstorming,
поэтому границы уточнения намерения и выбора подхода размыты.

## What Changes

- **BREAKING** Переименовать `usw-refine-task` в `usw-refine-intent` и обновить
  все package metadata, документацию, тесты и ссылки.
- Ограничить skill тремя обязанностями: вести диалог, уточнять ровно один
  decision case за ход и сохранять локальные ненормативные заметки.
- **BREAKING** Перенести default storage новых refinement sessions из
  `usw/refinements/` в `.usw/refinements/` и исключить его из shared
  provider/backlog configuration.
- Не создавать, не продвигать и не изменять backlog, OpenSpec, provider-owned
  planning artifacts или executable tasks без отдельного явного действия.
- Разрешать standard action `clarify-intent` в `usw-refine-intent`, а
  `usw-brainstorm-solutions` оставить за convergent action `select-approach`.
- Сохранить существующие shared refinement artifacts без автоматического
  перемещения, удаления или переписывания.

## Capabilities

### New Capabilities

- `intent-clarification`: Локальное диалоговое уточнение намерения, его
  ненормативные заметки, завершение без обязательного planning handoff и явная
  граница с оценкой решений и provider-owned artifacts.

### Modified Capabilities

Нет: в main `openspec/specs/` пока отсутствуют опубликованные capability specs.

## Impact

- Skill directory, frontmatter, assets and script currently under
  `skills/usw-refine-task/`.
- Default configuration and initialization rules for refinement storage.
- `usw-run-flow` capability registry and Analysis scenario behavior.
- README, package-layout/refinement/orchestration tests and extension metadata.
- Existing `usw/refinements/` data remains untouched and requires an explicit
  user-directed migration if it should be reused locally.
