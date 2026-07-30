# Task 1.1: Добавить двухфазный follow-up в usw-create-flow

## Artifact model

- `v1`

## Result

`usw-create-flow` сначала завершает requested flow, затем нейтрально предлагает
отдельный анализ и разделяет согласие на анализ от согласия на revision.

## Scope

- Обновить `skills/usw-create-flow/SKILL.md`.
- При необходимости синхронизировать `skills/usw-create-flow/agents/openai.yaml`.
- Сохранить ordinary/structured, shared/local и no-execution границы.

## Non-scope

- Создание отдельного analysis skill или runtime.
- Изменение `usw-run-flow`.
- Автоматическое применение рекомендаций.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/flow-authoring-assistance/spec.md`

## Dependencies

- Нет.

## Definition of done

- После успешного отчёта скилл предлагает будущий отдельный анализ без заявления
  о готовых идеях.
- Анализ запускается только после согласия и не меняет flow.
- Revision применяет только отдельно одобренные рекомендации.
- Рекомендации пропорциональны конкретным рискам.

## Verification

- Run: `python3 -m unittest tests.test_package_layout -v`
- Run: `python3 /Users/leonidkim/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/usw-create-flow`

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | implementation | `cr-001` | `usw-source-v1:f39d2e4e16948c71d5215ebceae0c812448c4c6c9369801626d70a9a8b954693` | verified | `development-evidence.md` |
| 2 | owner wording correction | `cr-001` | `usw-source-v1:b48ccd5ab5fab5ac5cb9c3ea7b5b9e1da07911944f383f664ed75d690edf9231` | verified | `development-evidence.md` |
| 3 | owner language correction | `cr-001` | `usw-source-v1:d3c54bb69a2ef3e05f9b6b71a4244cbfdc037b4c93949fe2cf5ffd8fb8a94a18` | verified | `development-evidence.md` |
