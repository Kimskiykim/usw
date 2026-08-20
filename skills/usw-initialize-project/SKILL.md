---
name: usw-initialize-project
description: Initialize a configured USW workspace and developer-local handoff state in the current project. Use when the usw-init command delegates initialization or the user asks to initialize USW in a project.
---

# Инициализация USW

Найти `scripts/init_usw.py` относительно этого `SKILL.md`. До первой записи в
проект выбрать интерпретатор:

1. Попробовать `python3`, затем `python`.
2. Для каждого кандидата выполнить
   `<candidate> -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'`.
3. Использовать первого кандидата, завершившегося успешно, и передать script-у
   текущий project root единственным аргументом.
4. Любой ненулевой результат `init_usw.py` — ошибка инициализации: сообщить её
   и остановиться; не скрывать ошибку script или configuration за fallback.

Если ни одна команда не даёт Python 3.10+, спросить пользователя на его языке,
продолжать ли LLM-инициализацией под тем же функциональным v1 contract.
Объяснить, что существующие файлы не будут перезаписаны, но исполнение менее
детерминировано. Ничего не записывать до явного согласия пользователя. После
согласия прочитать и выполнить
[references/llm-fallback.md](references/llm-fallback.md). При отказе
остановиться без изменений.

Сообщить, были ли `usw.yaml`, configured flow root, четыре flow examples,
`.usw/.gitignore` и, при включённом handoff, `.usw/HANDOFF.md` созданы или уже
существовали. Никогда не перезаписывать существующий файл. `.usw/flows/` и
`.usw/refinements/` создаются только при первом local flow или уточнении
намерения.

Optional top-level поле `handoff` принимает только boolean `true` или `false`;
отсутствие означает `true`. При включённом handoff создать `.usw/HANDOFF.md`
как детерминированный empty operation router. `.usw/handoffs/` остаётся lazy
до первого Begin. При выключенном — не читать, не проверять, не создавать и не
изменять оба пути и operation-scoped candidates.
`.usw/.gitignore` создаётся как удобный default; tracked/ignore state Git не
проверяется и не навязывается: политика tracking принадлежит пользователю.

Все configured roots и `.usw/` должны быть реальными директориями внутри
project root. Отклонить symlinks и пересекающиеся roots до первой managed
записи.

Capability boundary: входы — project root и существующая configuration;
разрешённые записи — initialization configuration, отсутствующий flow root,
ненормативные flow examples и developer-local initial state. Вернуть caller-у
созданные и уже существовавшие пути. Return point: после отчёта об
инициализации; не запускать flow и не вызывать другой skill.
Если инициализация упала после частичной записи, сообщить о возможном partial
workspace и порекомендовать устранить причину и повторить запуск:
create-only поведение сохраняет существующие файлы при retry.

Не создавать artifact storage заранее. В частности, инициализация не создаёт
`<artifacts.root>/changes/`, `<artifacts.root>/templates/`, `<reviews.root>/`
и `.usw/handoffs/`: точный destination создаёт та capability, которой он
впервые нужен.

Файлы в `templates/flows/examples/` — guidance, а не runtime fallback или
нормативные контракты flow. Скопировать в `<flows.root>/examples/` ровно
четыре packaged examples: `chat-review.md`, `dev-test.md`,
`plan-small-steps.md` и `refine-intent.md`. Никогда не создавать, не
мигрировать и не удалять legacy `flow-scenario-*.md` файлы.
