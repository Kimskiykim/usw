# Refinement outcome: Execution evidence open questions

- Refinement: `execution-evidence-open-questions`
- Status: ready
- Updated: 2026-07-21T12:43:49+03:00
- Target: OpenSpec change `establish-standalone-usw-workflow`

## Goal

Закрыть оставшиеся вопросы дизайна standalone USW workflow перед продолжением
реализации change.

## Agreed model

- Изменение contract revision или source identity задачи делает всё связанное
  Development и Testing evidence этой задачи stale.
- Старые evidence entries сохраняются как история, но все обязательные checks
  выполняются заново против текущих contract revision и source identity.
- OpenSpec `1.6.0` является первым точным release-blocking compatibility target.
- Latest OpenSpec проверяется отдельно, остаётся видимым и не блокирует release.
- v1 содержит только встроенные standalone и OpenSpec adapters.
- Declarative path mapping и executable provider/plugin API откладываются до
  появления второго реального provider consumer.

## Constraints

- Не удалять и не переписывать историческое evidence при invalidation.
- Не использовать evidence прежнего source или contract revision для завершения
  текущей попытки.
- Не изменять pinned OpenSpec version без явного обновления и успешного
  compatibility evidence.
- Неподдерживаемый provider должен завершаться structured error до записи и без
  standalone fallback.

## Remaining unknowns

- None within the scoped design questions.

## Decision references

- `D-001`
- `D-002`
- `D-003`

## Recommended next flow

Use `usw:openspec-update-change` to apply these three decisions coherently to
the existing planning artifacts, then run strict OpenSpec validation. Do not
modify product code in that flow.
