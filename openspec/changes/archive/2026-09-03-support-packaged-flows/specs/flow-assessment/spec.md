## MODIFIED Requirements

### Requirement: Assessment использует точно и безопасно разрешённый Markdown
USW SHALL предоставлять read-only loader, применяющий правила execution resolver:
kebab-case, совместимый layout, неоднозначность, containment,
descriptor-relative traversal, запрет symlink, требование regular file и UTF-8.
Loader SHALL возвращать `name`, `origin`, `identity`, `path`, точный абсолютный
`flow_directory`, точный `markdown` и `warnings` без execution input. Assessor
MUST использовать только возвращённый Markdown, MUST NOT повторно открывать
`path` или любой sibling package resource и SHALL сообщать о названном package
resource как о непроверенной зависимости. Inspection MUST NOT проверять legacy
state, HANDOFF или `.usw/FLOW.json`. Существующее поведение `resolve` для
flat flow MUST оставаться совместимым.

#### Scenario: Flow изменяется после inspection
- **WHEN** entrypoint изменяется после возврата точных Markdown и identity
- **THEN** assessment продолжается по возвращённым Markdown и identity

#### Scenario: Выбранный flow проходит через symlink
- **WHEN** origin root, package directory, intermediate component или final
  entrypoint является symlink
- **THEN** inspection останавливается до semantic assessment

#### Scenario: Инспектируется packaged flow
- **WHEN** assessment разрешает `<name>/FLOW.md`
- **THEN** его отчёт называет точный entrypoint и точный абсолютный
  `<flow-root>/<name>` как `flow_directory`, не читая sibling resources

#### Scenario: Packaged flow называет sibling resource
- **WHEN** инспектируемый packaged Markdown ссылается на `scripts/check.py`
- **THEN** assessment записывает непроверенную зависимость, не открывая этот
  script
