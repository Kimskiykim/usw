---
owner: maintainer
updated: 2026-09-23
---
# Глоссарий

- **Flow** — именованный Markdown-процесс, исполняемый моделью как текст.
- **Origin** — источник flow: local (`.usw/flows`) или shared (`flows.root`
  из `usw.yaml`).
- **Entrypoint / раскладка** — `<flow-root>/<name>.md` (flat) или
  `<flow-root>/<name>/FLOW.md` (canonical, package). Обе формы одного имени
  в одном origin → `ambiguous_flow_layout`.
- **Package** — каталог flow с `FLOW.md` и соседними файлами; исполнитель
  читает нужные файлы обычным инструментом относительно `flow_directory`.
- **version-2** — text-first авторская конвенция с маркерами `CALL`,
  `GATE`, `LOOP`, `PARALLEL`; подсказки модели, не machine DSL.
- **Contract tokens** — дословные статусы и варианты ответа человека в
  обратных кавычках (`approve`, `change`, `blocked`…); не переводятся.
- **Design scan** — read-only разбор сохранённого flow по каталогу рецептов
  с ≤3 подсказками.
- **Рецепт (recipe)** — переиспользуемый блок проектирования flow из
  `skills/usw-create-flow/references/recipes/`.
- **Handoff / router** — `.usw/HANDOFF.md`, validated Markdown-маршрутизатор
  от operation identity к state-файлу под `.usw/handoffs/`.
- **Operation** — один top-level запуск flow с уникальной identity и
  собственным state; child flow использует identity root и durable state
  не пишет.
- **Task contract / tasks.md** — единственный completion source исполнения
  (см. спеку execution-artifacts).
- **USW-SOURCE-V1** — identity продуктового источника в артефактах
  исполнения.
- **Stable-token тесты** — детерминированные тесты в `tests/`, фиксирующие
  контрактные токены и структуры нормативных текстов.
- **Behavior evals** — локальные платные прогоны `evals/`, измеряющие,
  следует ли модель инструкциям `SKILL.md`; наблюдение, не гейт.
- **Executor / runner** — модель в агентском CLI, исполняющая flow.
