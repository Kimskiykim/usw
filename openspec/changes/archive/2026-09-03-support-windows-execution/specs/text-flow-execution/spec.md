## MODIFIED Requirements

### Requirement: Безопасное разрешение text flow
USW SHALL разрешать только safe kebab-case name как `<name>.md` или
`<name>/FLOW.md` внутри выбранного local или shared root. Он MUST проверять
containment и каждый существующий path component, отклонять symbolic links и
требовать regular final entrypoint до чтения. Traversal и final read SHALL
проходить через общую safe-access boundary: descriptor-relative без повторного
открытия pathname после признания component доверенным на платформах с
`dir_fd`, либо pathname-based с отклонением reparse point для каждого component
и повторной проверкой containment на остальных платформах. Если в одном
выбранном origin существуют оба layout, разрешение MUST остановиться с
`ambiguous_flow_layout`. Оба flow layout и packaged resources SHALL разрешаться
на каждой поддерживаемой платформе; `unsupported_safe_flow_platform` MUST NOT
быть обычным результатом разрешения packaged flow на поддерживаемой платформе.

#### Scenario: Промежуточный symlink
- **WHEN** любой component, ведущий к выбранному flat или packaged flow, является symbolic link
- **THEN** USW останавливается до чтения flow или вызова модели

#### Scenario: Существуют оба layout
- **WHEN** один выбранный origin содержит safe flat и packaged entrypoints для запрошенного имени
- **THEN** USW возвращает `ambiguous_flow_layout`, не читая ни один из них как выбранный invocation

#### Scenario: Packaged flow без descriptor-relative access
- **WHEN** packaged `<name>/FLOW.md` разрешается на поддерживаемой платформе без `dir_fd`
- **THEN** USW использует pathname-based backend и возвращает те же name, origin, identity, path, flow directory и точный Markdown, что и на остальных платформах

#### Scenario: Packaged resource без descriptor-relative access
- **WHEN** packaged Markdown называет sibling resource на такой платформе
- **THEN** resource читается через ту же boundary, привязывается к исходным flow identity и entrypoint и отклоняется при link, escape или неожиданном filesystem type

#### Scenario: Windows fallback разрешает legacy flat flow
- **WHEN** descriptor-relative API недоступны и существует только совместимый entrypoint `<name>.md`
- **THEN** USW разрешает его через pathname-based backend с теми же проверками containment, link и filesystem type, что и на descriptor-relative backend
