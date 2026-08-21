# Ограниченная LLM-инициализация

Использовать этот путь только после того, как и `python3`, и `python` не прошли
проверку версии Python 3.10+, а пользователь явно принял сниженные гарантии.
Никогда не использовать его после того, как `init_usw.py` запустился или
вернул ошибку.

## Preflight

1. Использовать переданный корень открытого проекта.
2. Разрешать все пути относительно этого root. До первой записи отклонить
   существующий symbolic link, специальный filesystem object, absolute target
   и traversal через `.` или `..`.
3. Если `usw.yaml` отсутствует, выбрать packaged standalone v1 configuration.
   Иначе прочитать его без изменений и применить тот же supported v1 contract,
   что и Python-инициализатор:
   - требовать `schema_version: 1`;
   - отклонять удалённое поле `artifacts.provider`;
   - отсутствующий `artifacts.root` разрешать в `usw`;
   - отсутствующие `flows.root` и `reviews.root` разрешать в `usw/flows` и
     `usw/reviews`;
   - принимать optional top-level `handoff` только как unquoted boolean
     `true` или `false`; отсутствие поля означает `true`;
   - принимать безопасные custom artifact, flow и review roots;
   - игнорировать legacy `refinement` и неизвестные поля, не используя их для
     создания или миграции state.
4. Проверить artifact, flow и review roots вместе. Они должны быть
   project-relative путями к реальным директориям вне `.git` и `.usw`; flow и
   review roots не должны пересекаться. Flow и review roots могут быть
   потомками artifact root, но любое другое пересечение writable roots
   недопустимо.
5. Классифицировать каждый destination и его parent до записи. Принимать
   только отсутствующие пути, regular files на местах файлов и реальные
   директории на местах директорий. Существующие regular files сохранять
   byte-for-byte.

Не проверять и не навязывать Git tracked/ignore state. Генерируемый
`.usw/.gitignore` — удобство; политика tracking репозитория принадлежит
пользователю.

## Материализация configured v1 workspace

Создавать только отсутствующие пути:

- если configuration отсутствовала, скопировать packaged `templates/usw.yaml`
  в `usw.yaml`;
- создать configured flow root;
- создать `.usw/.gitignore` с `*` и завершающим переводом строки;
- создать `<flows.root>/examples/` и скопировать туда ровно четыре packaged
  examples: `chat-review.md`, `dev-test.md`, `plan-small-steps.md` и
  `refine-intent.md`.

Не создавать `<artifacts.root>/changes/`, `<artifacts.root>/templates/`,
`<reviews.root>/` и `.usw/handoffs/`: точный destination создаёт та
capability, которой он впервые нужен.

При effective `handoff: true` скопировать детерминированный empty router из
packaged `templates/local/HANDOFF.md` в отсутствующий `.usw/HANDOFF.md`. Не
создавать `.usw/handoffs/`: Begin создаёт его лениво. При `handoff: false` не
читать, не проверять, не создавать и не изменять `.usw/HANDOFF.md`,
`.usw/handoffs/` и operation-scoped candidates.

Никогда не перезаписывать, не сливать, не удалять, не выполнять chmod и не
следовать links. Не создавать `.usw/flows/`, `.usw/refinements/` и
`.usw/handoffs/`. Не создавать, не мигрировать и не удалять legacy
`flow-scenario-*.md` файлы. Каждый установленный example ненормативен и должен
оставаться вложенным в `examples/`, чтобы runner не мог выбрать его напрямую
по flat имени flow.

## Проверка и отчёт

Перечитать каждый созданный файл. При включённом handoff убедиться, что
`.usw/HANDOFF.md` — точный packaged empty router и `.usw/handoffs/` не создан;
при выключенном — убедиться только по write inventory, что handoff-пути не
тронуты. Убедиться, что каждый существовавший destination остался
byte-for-byte неизменным. Сообщить, что использован ограниченный LLM fallback
с меньшей детерминированностью, чем Python, и перечислить созданные и
сохранённые пути раздельно.

Если какая-то запись упала, сообщить, что workspace может быть
инициализирован частично, предложить устранить причину и повторить
инициализацию; существующие файлы при retry сохраняются. Вернуться, не
запуская flow.
