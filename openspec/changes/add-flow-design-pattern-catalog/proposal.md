# Proposal

## Why

Рецепты USW уже описывают многие способы организации работы, но при создании flow нет общего словаря, связывающего их с именованными паттернами и условиями применения. Пользователю трудно обсуждать выбор структуры и отличать известный паттерн от адаптации USW.

## What Changes

- Добавить каталог с полным покрытием именованных подходов из исходного вложения и дополнения Anthropic: русские названия, исходные имена, происхождение и ссылки.
- Различить паттерн, рецепт и конкретный flow; связать каталог с существующими рецептами без второй копии их инструкций.
- Охватить Pipeline / Prompt chaining, Routing / Dispatcher, Sectioning, Voting, Supervisor / Orchestrator–workers, Evaluator–optimizer, Maker–checker, Claim Check и Fan-out / Fan-in.
- Добавить Hierarchical decomposition, Handoff, Group chat / Debate / Council, Planner–executor–replanner, Blackboard, общую очередь задач и изоляцию контекста субагентов. Различить варианты, композиции, механизмы контекста и режим автономного управления.
- Для каждого подхода указать рецепт, композицию либо необходимые возможности среды; отсутствие поддержки не исключает подход из каталога и не разрешает имитировать её.
- При создании flow и design scan объяснять выбор применимых паттернов, затем показывать конкретные шаги в выбранном стиле.
- Сохранить простоту по умолчанию, ограниченное чтение, контроль записи человеком и границы исполнения USW.

## Scope

Каталог, таблица покрытия исходных названий, адаптация рецептов, guidance в `usw-create-flow`, краткие определения и проверка поведения автора flow. Полнота каталога отделена от доступности исполнения: описать подход и его ограничения необходимо даже при отсутствии нужных возможностей среды. Принципы оркестрации через артефакты остаются правилами проектирования; этот change не реализует новый протокол исполнения.

## Non-goals

- Runtime, DSL, scheduler, реестр паттернов в коде, машинное голосование или гарантии исполнения.
- Новые обязательные поля flow/frontmatter, изменение handoff, execution-artifacts или политики повторов runner.
- Автоматический запуск flow, получение новых полномочий, миграция существующих flow или изменение их human gates.
- Рекурсивная энциклопедия всех терминов всех связанных сайтов; граница покрытия — именованные подходы первого вложения и Building effective agents. Полный протокол отчётов и версионирования рассматривается отдельно.

## Capabilities

### New Capabilities

- `flow-design-patterns`: компактный каталог именованных способов проектирования, их происхождение, различия, условия выбора и связь с рецептами USW.

### Modified Capabilities

- `guided-flow-authoring`: применение словаря паттернов при проектировании от цели и bounded design scan без изменения полномочий и согласования записи.

## Impact

Затрагиваются исходные `skills/usw-create-flow/SKILL.md`, его `references/`, глоссарий и краткая навигация README; детерминированные проверки структуры и поведения в `tests/` и сценарии `evals/`. CLI, Python runner и установка не требуют новых зависимостей. Изменения совместимы с существующими flow.

Основания: обсуждение пользователя и полный приложенный текст об оркестрации; [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents), [Claim Check](https://www.enterpriseintegrationpatterns.com/patterns/messaging/StoreInLibrary.html), [ADK](https://adk.dev/workflows/patterns/), [Microsoft](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns), [LangChain](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents), [Blackboard](https://www.cs.cmu.edu/~ModProb/MRsol4.html), [общая очередь в эксперименте Anthropic](https://www.anthropic.com/engineering/building-c-compiler). Источники обосновывают терминологию; спецификации USW определяют локальные контракты.
