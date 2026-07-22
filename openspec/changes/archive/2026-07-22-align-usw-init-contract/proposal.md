## Why

`/usw-init` сейчас смешивает создание workspace с навязыванием Git privacy policy, расходится с LLM fallback и содержит устаревшие refinement и OpenSpec-инструкции. Контракт нужно привести к фактической provider-neutral модели до дальнейшего развития initialization, чтобы Python и agent paths создавали одинаковый v1 workspace и не принимали решения за пользователя.

## What Changes

- Ввести явный контракт project initialization с точным набором немедленно и лениво создаваемых артефактов, additive/idempotent поведением и понятным восстановлением после частичной I/O-ошибки.
- Оставить создание `.usw/.gitignore` как удобство, но убрать Git tracked/ignore enforcement: итоговая tracking policy принадлежит пользователю.
- **BREAKING** удалить legacy shared `refinement.root` и capability `task-refinement`; новые clarification sessions остаются только в `.usw/refinements/`, а исторические shared sessions не мигрируются автоматически.
- Сделать Python и LLM initialization функционально эквивалентными для всех поддерживаемых v1 configurations, включая наличие или выбор OpenSpec provider; различие ограничивается явно сообщаемыми гарантиями детерминированности.
- Считать `openspec/` только directory hint при initialization и не валидировать provider workspace заранее. Detection и OpenSpec provider не изменяют provider-owned artifacts; explicit standalone custom roots остаются пользовательским выбором. Required artifacts проверяются конкретными provider operations.
- Сделать OpenSpec messaging provider-aware, обновить repo-local `openspec/AGENTS.md` и удалить недостижимый packaged OpenSpec AGENTS template.
- Исправить README inventory и regression-тест `chat-review`, добавив ожидания третьего action и трёх GATE routes.
- Не добавлять transactional initialization и concurrent symlink TOCTOU hardening: безопасный повторный запуск и существующая static symlink protection остаются принятыми границами.

## Capabilities

### New Capabilities

- `project-initialization`: Контракт `/usw-init`, artifact inventory, Python/LLM parity, user-owned Git policy, partial-failure recovery и provider-scoped OpenSpec no-write boundary.

### Modified Capabilities

- `workspace-configuration`: Удаление активного `refinement.root`, Git privacy enforcement и утверждения о валидности любого `openspec/` каталога; сохранение безопасных configured roots и explicit provider selection.
- `intent-clarification`: Локальные `.usw/refinements/` остаются ненормативными, но tracking policy больше не проверяется capability автоматически.
- `task-refinement`: Удаление legacy shared refinement capability в пользу `intent-clarification` без автоматической миграции исторических sessions.

## Impact

- Initialization implementation and fallback: `skills/usw-initialize-project/` и `commands/usw-init.md`.
- Local clarification storage: `skills/usw-refine-intent/`.
- Tests: `tests/test_init_usw.py`, `tests/test_refine_task.py`, `tests/test_flow_scenarios.py` и полный unittest suite.
- Documentation and packaged assets: `README.md`, `openspec/AGENTS.md`, packaged OpenSpec AGENTS template.
- Main specs: `workspace-configuration`, `intent-clarification`, удаляемый `task-refinement`, плюс новый `project-initialization`.
- Не затрагиваются provider-owned OpenSpec artifacts, если пользователь явно не выбрал этот namespace как standalone custom root; provider adapters, static symlink protection и transactional semantics также не меняются.
