**Инвентаризация скиллов и промптов USW**

Дата: 3 октября 2026. Исходная ревизия: `db38d99`.

Реестр области статического разбора. Копии учтены отдельно, поскольку агент может загрузить разные версии. Исторические инструкции рассмотрены как снятый контракт; их runtime не проверялся. Спецификации, реализация, тесты и metadata использованы дополнительно для сверки, но не включены в число Markdown-инструкций.

**Поставляемые skills, references, рецепты и шаблоны — 41 файлов**

| Файл | Строк |
| --- | ---: |
| [skills/usw-assess-flow/SKILL.md](/Users/leonidkim/Documents/projects/usw/skills/usw-assess-flow/SKILL.md) | 221 |
| [skills/usw-assess-flow/references/assessment-model.md](/Users/leonidkim/Documents/projects/usw/skills/usw-assess-flow/references/assessment-model.md) | 26 |
| [skills/usw-create-flow/SKILL.md](/Users/leonidkim/Documents/projects/usw/skills/usw-create-flow/SKILL.md) | 183 |
| [skills/usw-create-flow/references/recipes/adaptive-intensity.md](/Users/leonidkim/Documents/projects/usw/skills/usw-create-flow/references/recipes/adaptive-intensity.md) | 25 |
| [skills/usw-create-flow/references/recipes/bounded-refinement.md](/Users/leonidkim/Documents/projects/usw/skills/usw-create-flow/references/recipes/bounded-refinement.md) | 17 |
| [skills/usw-create-flow/references/recipes/capability-reuse.md](/Users/leonidkim/Documents/projects/usw/skills/usw-create-flow/references/recipes/capability-reuse.md) | 13 |
| [skills/usw-create-flow/references/recipes/error-handling.md](/Users/leonidkim/Documents/projects/usw/skills/usw-create-flow/references/recipes/error-handling.md) | 16 |
| [skills/usw-create-flow/references/recipes/escalation.md](/Users/leonidkim/Documents/projects/usw/skills/usw-create-flow/references/recipes/escalation.md) | 19 |
| [skills/usw-create-flow/references/recipes/external-action-approval.md](/Users/leonidkim/Documents/projects/usw/skills/usw-create-flow/references/recipes/external-action-approval.md) | 16 |
| [skills/usw-create-flow/references/recipes/external-event-wait.md](/Users/leonidkim/Documents/projects/usw/skills/usw-create-flow/references/recipes/external-event-wait.md) | 17 |
| [skills/usw-create-flow/references/recipes/human-decision.md](/Users/leonidkim/Documents/projects/usw/skills/usw-create-flow/references/recipes/human-decision.md) | 13 |
| [skills/usw-create-flow/references/recipes/independent-checks.md](/Users/leonidkim/Documents/projects/usw/skills/usw-create-flow/references/recipes/independent-checks.md) | 14 |
| [skills/usw-create-flow/references/recipes/input-preflight.md](/Users/leonidkim/Documents/projects/usw/skills/usw-create-flow/references/recipes/input-preflight.md) | 16 |
| [skills/usw-create-flow/references/recipes/list-processing.md](/Users/leonidkim/Documents/projects/usw/skills/usw-create-flow/references/recipes/list-processing.md) | 17 |
| [skills/usw-create-flow/references/recipes/result-check.md](/Users/leonidkim/Documents/projects/usw/skills/usw-create-flow/references/recipes/result-check.md) | 14 |
| [skills/usw-create-flow/references/recipes/subagent-orchestration.md](/Users/leonidkim/Documents/projects/usw/skills/usw-create-flow/references/recipes/subagent-orchestration.md) | 77 |
| [skills/usw-create-flow/references/recipes/subagent-review.md](/Users/leonidkim/Documents/projects/usw/skills/usw-create-flow/references/recipes/subagent-review.md) | 29 |
| [skills/usw-create-flow/references/recipes/variant-selection.md](/Users/leonidkim/Documents/projects/usw/skills/usw-create-flow/references/recipes/variant-selection.md) | 19 |
| [skills/usw-create-flow/references/recipes.md](/Users/leonidkim/Documents/projects/usw/skills/usw-create-flow/references/recipes.md) | 49 |
| [skills/usw-create-flow/references/version-2.md](/Users/leonidkim/Documents/projects/usw/skills/usw-create-flow/references/version-2.md) | 44 |
| [skills/usw-find-flow/SKILL.md](/Users/leonidkim/Documents/projects/usw/skills/usw-find-flow/SKILL.md) | 81 |
| [skills/usw-initialize-project/SKILL.md](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/SKILL.md) | 67 |
| [skills/usw-initialize-project/references/llm-fallback.md](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/references/llm-fallback.md) | 83 |
| [skills/usw-initialize-project/templates/change/design.md](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/templates/change/design.md) | 29 |
| [skills/usw-initialize-project/templates/change/proposal.md](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/templates/change/proposal.md) | 17 |
| [skills/usw-initialize-project/templates/change/spec.md](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/templates/change/spec.md) | 22 |
| [skills/usw-initialize-project/templates/change/tasks.md](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/templates/change/tasks.md) | 8 |
| [skills/usw-initialize-project/templates/flows/examples/README.md](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/templates/flows/examples/README.md) | 7 |
| [skills/usw-initialize-project/templates/flows/examples/chat-review.md](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/templates/flows/examples/chat-review.md) | 212 |
| [skills/usw-initialize-project/templates/flows/examples/dev-test.md](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/templates/flows/examples/dev-test.md) | 53 |
| [skills/usw-initialize-project/templates/flows/examples/plan-small-steps.md](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/templates/flows/examples/plan-small-steps.md) | 50 |
| [skills/usw-initialize-project/templates/flows/examples/refine-intent.md](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/templates/flows/examples/refine-intent.md) | 35 |
| [skills/usw-initialize-project/templates/local/HANDOFF.md](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/templates/local/HANDOFF.md) | 15 |
| [skills/usw-initialize-project/templates/review/receipt.md](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/templates/review/receipt.md) | 22 |
| [skills/usw-initialize-project/templates/task/development-evidence.md](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/templates/task/development-evidence.md) | 7 |
| [skills/usw-initialize-project/templates/task/task.md](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/templates/task/task.md) | 46 |
| [skills/usw-initialize-project/templates/task/testing-evidence.md](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/templates/task/testing-evidence.md) | 7 |
| [skills/usw-manage-handoff/SKILL.md](/Users/leonidkim/Documents/projects/usw/skills/usw-manage-handoff/SKILL.md) | 162 |
| [skills/usw-manage-handoff/references/state-model.md](/Users/leonidkim/Documents/projects/usw/skills/usw-manage-handoff/references/state-model.md) | 55 |
| [skills/usw-run-flow/SKILL.md](/Users/leonidkim/Documents/projects/usw/skills/usw-run-flow/SKILL.md) | 175 |
| [skills/usw-run-flow/references/execution-model.md](/Users/leonidkim/Documents/projects/usw/skills/usw-run-flow/references/execution-model.md) | 38 |

**Командные промпты — 10 файлов**

| Файл | Строк |
| --- | ---: |
| [commands/usw-assess-flow.md](/Users/leonidkim/Documents/projects/usw/commands/usw-assess-flow.md) | 8 |
| [commands/usw-bounded-implementer.md](/Users/leonidkim/Documents/projects/usw/commands/usw-bounded-implementer.md) | 51 |
| [commands/usw-coverage-checker.md](/Users/leonidkim/Documents/projects/usw/commands/usw-coverage-checker.md) | 54 |
| [commands/usw-find-flow.md](/Users/leonidkim/Documents/projects/usw/commands/usw-find-flow.md) | 8 |
| [commands/usw-handoff.md](/Users/leonidkim/Documents/projects/usw/commands/usw-handoff.md) | 16 |
| [commands/usw-hypothesis-checker.md](/Users/leonidkim/Documents/projects/usw/commands/usw-hypothesis-checker.md) | 50 |
| [commands/usw-init.md](/Users/leonidkim/Documents/projects/usw/commands/usw-init.md) | 7 |
| [commands/usw-resume.md](/Users/leonidkim/Documents/projects/usw/commands/usw-resume.md) | 14 |
| [commands/usw-reviewer-llm-critic.md](/Users/leonidkim/Documents/projects/usw/commands/usw-reviewer-llm-critic.md) | 64 |
| [commands/usw-scout.md](/Users/leonidkim/Documents/projects/usw/commands/usw-scout.md) | 46 |

**Проектные flow и примеры — 13 файлов**

| Файл | Строк |
| --- | ---: |
| [usw/flows/chat-review.md](/Users/leonidkim/Documents/projects/usw/usw/flows/chat-review.md) | 212 |
| [usw/flows/code-improvement-audit.md](/Users/leonidkim/Documents/projects/usw/usw/flows/code-improvement-audit.md) | 301 |
| [usw/flows/dev-test.md](/Users/leonidkim/Documents/projects/usw/usw/flows/dev-test.md) | 56 |
| [usw/flows/discussion-with-todo.md](/Users/leonidkim/Documents/projects/usw/usw/flows/discussion-with-todo.md) | 68 |
| [usw/flows/examples/README.md](/Users/leonidkim/Documents/projects/usw/usw/flows/examples/README.md) | 7 |
| [usw/flows/examples/chat-review.md](/Users/leonidkim/Documents/projects/usw/usw/flows/examples/chat-review.md) | 212 |
| [usw/flows/examples/dev-test.md](/Users/leonidkim/Documents/projects/usw/usw/flows/examples/dev-test.md) | 53 |
| [usw/flows/examples/plan-small-steps.md](/Users/leonidkim/Documents/projects/usw/usw/flows/examples/plan-small-steps.md) | 50 |
| [usw/flows/examples/refine-intent.md](/Users/leonidkim/Documents/projects/usw/usw/flows/examples/refine-intent.md) | 35 |
| [usw/flows/intent-to-spec.md](/Users/leonidkim/Documents/projects/usw/usw/flows/intent-to-spec.md) | 373 |
| [usw/flows/project-self-improvement/FLOW.md](/Users/leonidkim/Documents/projects/usw/usw/flows/project-self-improvement/FLOW.md) | 20 |
| [usw/flows/review-fix-and-backlog.md](/Users/leonidkim/Documents/projects/usw/usw/flows/review-fix-and-backlog.md) | 62 |
| [usw/flows/review-walkthrough/FLOW.md](/Users/leonidkim/Documents/projects/usw/usw/flows/review-walkthrough/FLOW.md) | 59 |

**Cookbook — 2 файлов**

| Файл | Строк |
| --- | ---: |
| [usw/cookbook/context-packs.md](/Users/leonidkim/Documents/projects/usw/usw/cookbook/context-packs.md) | 261 |
| [usw/cookbook/selective-superpowers.md](/Users/leonidkim/Documents/projects/usw/usw/cookbook/selective-superpowers.md) | 125 |

**OpenSpec в .agents — 12 файлов**

| Файл | Строк |
| --- | ---: |
| [.agents/skills/openspec-apply-change/SKILL.md](/Users/leonidkim/Documents/projects/usw/.agents/skills/openspec-apply-change/SKILL.md) | 188 |
| [.agents/skills/openspec-archive-change/SKILL.md](/Users/leonidkim/Documents/projects/usw/.agents/skills/openspec-archive-change/SKILL.md) | 182 |
| [.agents/skills/openspec-bulk-archive-change/SKILL.md](/Users/leonidkim/Documents/projects/usw/.agents/skills/openspec-bulk-archive-change/SKILL.md) | 339 |
| [.agents/skills/openspec-continue-change/SKILL.md](/Users/leonidkim/Documents/projects/usw/.agents/skills/openspec-continue-change/SKILL.md) | 118 |
| [.agents/skills/openspec-explore/SKILL.md](/Users/leonidkim/Documents/projects/usw/.agents/skills/openspec-explore/SKILL.md) | 311 |
| [.agents/skills/openspec-ff-change/SKILL.md](/Users/leonidkim/Documents/projects/usw/.agents/skills/openspec-ff-change/SKILL.md) | 113 |
| [.agents/skills/openspec-new-change/SKILL.md](/Users/leonidkim/Documents/projects/usw/.agents/skills/openspec-new-change/SKILL.md) | 77 |
| [.agents/skills/openspec-onboard/SKILL.md](/Users/leonidkim/Documents/projects/usw/.agents/skills/openspec-onboard/SKILL.md) | 561 |
| [.agents/skills/openspec-propose/SKILL.md](/Users/leonidkim/Documents/projects/usw/.agents/skills/openspec-propose/SKILL.md) | 149 |
| [.agents/skills/openspec-sync-specs/SKILL.md](/Users/leonidkim/Documents/projects/usw/.agents/skills/openspec-sync-specs/SKILL.md) | 262 |
| [.agents/skills/openspec-update-change/SKILL.md](/Users/leonidkim/Documents/projects/usw/.agents/skills/openspec-update-change/SKILL.md) | 91 |
| [.agents/skills/openspec-verify-change/SKILL.md](/Users/leonidkim/Documents/projects/usw/.agents/skills/openspec-verify-change/SKILL.md) | 175 |

**OpenSpec в .codex — 12 файлов**

| Файл | Строк |
| --- | ---: |
| [.codex/skills/openspec-apply-change/SKILL.md](/Users/leonidkim/Documents/projects/usw/.codex/skills/openspec-apply-change/SKILL.md) | 160 |
| [.codex/skills/openspec-archive-change/SKILL.md](/Users/leonidkim/Documents/projects/usw/.codex/skills/openspec-archive-change/SKILL.md) | 118 |
| [.codex/skills/openspec-bulk-archive-change/SKILL.md](/Users/leonidkim/Documents/projects/usw/.codex/skills/openspec-bulk-archive-change/SKILL.md) | 249 |
| [.codex/skills/openspec-continue-change/SKILL.md](/Users/leonidkim/Documents/projects/usw/.codex/skills/openspec-continue-change/SKILL.md) | 122 |
| [.codex/skills/openspec-explore/SKILL.md](/Users/leonidkim/Documents/projects/usw/.codex/skills/openspec-explore/SKILL.md) | 290 |
| [.codex/skills/openspec-ff-change/SKILL.md](/Users/leonidkim/Documents/projects/usw/.codex/skills/openspec-ff-change/SKILL.md) | 105 |
| [.codex/skills/openspec-new-change/SKILL.md](/Users/leonidkim/Documents/projects/usw/.codex/skills/openspec-new-change/SKILL.md) | 77 |
| [.codex/skills/openspec-onboard/SKILL.md](/Users/leonidkim/Documents/projects/usw/.codex/skills/openspec-onboard/SKILL.md) | 555 |
| [.codex/skills/openspec-propose/SKILL.md](/Users/leonidkim/Documents/projects/usw/.codex/skills/openspec-propose/SKILL.md) | 114 |
| [.codex/skills/openspec-sync-specs/SKILL.md](/Users/leonidkim/Documents/projects/usw/.codex/skills/openspec-sync-specs/SKILL.md) | 148 |
| [.codex/skills/openspec-update-change/SKILL.md](/Users/leonidkim/Documents/projects/usw/.codex/skills/openspec-update-change/SKILL.md) | 86 |
| [.codex/skills/openspec-verify-change/SKILL.md](/Users/leonidkim/Documents/projects/usw/.codex/skills/openspec-verify-change/SKILL.md) | 172 |

**Навык разработки Git sync и references — 4 файлов**

| Файл | Строк |
| --- | ---: |
| [dev/skills/export-external-sync-bundles/SKILL.md](/Users/leonidkim/Documents/projects/usw/dev/skills/export-external-sync-bundles/SKILL.md) | 49 |
| [dev/skills/export-external-sync-bundles/references/repository-contract.md](/Users/leonidkim/Documents/projects/usw/dev/skills/export-external-sync-bundles/references/repository-contract.md) | 57 |
| [dev/skills/export-external-sync-bundles/references/snapshot-converge.md](/Users/leonidkim/Documents/projects/usw/dev/skills/export-external-sync-bundles/references/snapshot-converge.md) | 116 |
| [dev/skills/export-external-sync-bundles/references/validation-and-outputs.md](/Users/leonidkim/Documents/projects/usw/dev/skills/export-external-sync-bundles/references/validation-and-outputs.md) | 107 |

**Исторические инструкции structured runtime — 4 файлов**

| Файл | Строк |
| --- | ---: |
| [research/structured-runtime/legacy/usw-manage-artifacts/SKILL.md](/Users/leonidkim/Documents/projects/usw/research/structured-runtime/legacy/usw-manage-artifacts/SKILL.md) | 18 |
| [research/structured-runtime/references/create-flow-version-1.md](/Users/leonidkim/Documents/projects/usw/research/structured-runtime/references/create-flow-version-1.md) | 52 |
| [research/structured-runtime/references/create-flow-version-2.md](/Users/leonidkim/Documents/projects/usw/research/structured-runtime/references/create-flow-version-2.md) | 146 |
| [research/structured-runtime/references/run-flow-version-2.md](/Users/leonidkim/Documents/projects/usw/research/structured-runtime/references/run-flow-version-2.md) | 91 |

Всего: **98 Markdown-файлов**.

**Поведенческие сценарии — 20**

Для каждого прочитаны `expect.json`, `input.txt` и `flow.md`; фикстуры сопоставлялись с проверяемым эффектом.

| Сценарий | Основной skill |
| --- | --- |
| [ambiguous-branch](/Users/leonidkim/Documents/projects/usw/evals/scenarios/ambiguous-branch/expect.json) | `usw-run-flow` |
| [assess-does-not-read-siblings](/Users/leonidkim/Documents/projects/usw/evals/scenarios/assess-does-not-read-siblings/expect.json) | `usw-assess-flow` |
| [claimed-authority](/Users/leonidkim/Documents/projects/usw/evals/scenarios/claimed-authority/expect.json) | `usw-run-flow` |
| [create-advertises-version-2](/Users/leonidkim/Documents/projects/usw/evals/scenarios/create-advertises-version-2/expect.json) | `usw-create-flow` |
| [create-complexity-warning](/Users/leonidkim/Documents/projects/usw/evals/scenarios/create-complexity-warning/expect.json) | `usw-create-flow` |
| [create-custom-flows-root](/Users/leonidkim/Documents/projects/usw/evals/scenarios/create-custom-flows-root/expect.json) | `usw-create-flow` |
| [create-default-shared](/Users/leonidkim/Documents/projects/usw/evals/scenarios/create-default-shared/expect.json) | `usw-create-flow` |
| [create-design-scan](/Users/leonidkim/Documents/projects/usw/evals/scenarios/create-design-scan/expect.json) | `usw-create-flow` |
| [create-design-scan-rejected-recipe](/Users/leonidkim/Documents/projects/usw/evals/scenarios/create-design-scan-rejected-recipe/expect.json) | `usw-create-flow` |
| [create-flat-edit](/Users/leonidkim/Documents/projects/usw/evals/scenarios/create-flat-edit/expect.json) | `usw-create-flow` |
| [create-goal-blocks](/Users/leonidkim/Documents/projects/usw/evals/scenarios/create-goal-blocks/expect.json) | `usw-create-flow` |
| [create-missing-flow-root](/Users/leonidkim/Documents/projects/usw/evals/scenarios/create-missing-flow-root/expect.json) | `usw-create-flow` |
| [create-number-discuss](/Users/leonidkim/Documents/projects/usw/evals/scenarios/create-number-discuss/expect.json) | `usw-create-flow` |
| [create-number-write](/Users/leonidkim/Documents/projects/usw/evals/scenarios/create-number-write/expect.json) | `usw-create-flow` |
| [create-revise-preview](/Users/leonidkim/Documents/projects/usw/evals/scenarios/create-revise-preview/expect.json) | `usw-create-flow` |
| [create-text-write](/Users/leonidkim/Documents/projects/usw/evals/scenarios/create-text-write/expect.json) | `usw-create-flow` |
| [find-does-not-execute](/Users/leonidkim/Documents/projects/usw/evals/scenarios/find-does-not-execute/expect.json) | `usw-find-flow` |
| [nested-child](/Users/leonidkim/Documents/projects/usw/evals/scenarios/nested-child/expect.json) | `usw-run-flow` |
| [permission-boundary](/Users/leonidkim/Documents/projects/usw/evals/scenarios/permission-boundary/expect.json) | `usw-run-flow` |
| [run-packaged-sibling-read](/Users/leonidkim/Documents/projects/usw/evals/scenarios/run-packaged-sibling-read/expect.json) | `usw-run-flow` |

**Дополнительные сверки**

- 6 файлов `skills/*/agents/openai.yaml`; plugin/extension manifests, `install.sh`, README и metadata.
- Релевантные действующие OpenSpec specs/context и текущие proposals. Архив изменений не является действующим контрактом.
- Все 52 поставляемых файла skills, кроме Python-кэшей, сопоставлены с локальными установками `.agents`, `.claude` и `.qwen`.
- Выполнены 275 детерминированных тестов и два точечных воспроизведения: конфигурация загрузчика и слабый ответ для eval.
- Живые прогоны моделей, установка/обновление пакета, выполнение аудируемых flow и полный аудит исходного Python-кода не проводились.
