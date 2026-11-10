# AUD-T08 — Две действующие спецификации назначают разные места recovery state

- Статус: исправлена
- Приоритет: P2
- Категория: статический конфликт
- Действие: Согласовать recovery owner в execution-artifacts с routed operation contract.
- Условие возврата: следующая правка specs
- Критерий готовности: pause/replanning направлены в operation document, HANDOFF остаётся router; всю artifact-спеку архивной не объявлять.
- Источник: [Аудит T08](/Users/leonidkim/Documents/projects/usw/usw/reviews/skills-prompts-audit-2026-10-03/DATA_AND_CONTRACTS.md:78)
- Результат: [execution-artifacts](../../openspec/specs/execution-artifacts/spec.md) направляет pause и replanning в operation document; HANDOFF остаётся router.
- Границы: исправлен статический конфликт спецификаций; порча state и изменения backend не утверждаются. Независимые проверки и приёмка выполняются отдельно.
