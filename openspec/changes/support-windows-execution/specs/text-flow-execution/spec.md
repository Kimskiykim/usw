## MODIFIED Requirements

### Requirement: Безопасное разрешение text flow
USW SHALL разрешать только safe kebab-case name внутри выбранного local или
shared root. Он MUST проверять containment и каждый существующий path component,
отклонять symbolic links и требовать regular final file до чтения. Traversal и
final read SHALL проходить через общую safe-access boundary: descriptor-relative
без повторного открытия pathname после признания component доверенным на
платформах с `dir_fd`, либо pathname-based с отклонением reparse point для
каждого component и повторной проверкой containment на остальных платформах.
Оба flow layout и packaged resources SHALL разрешаться на каждой поддерживаемой
платформе; `unsupported_safe_flow_platform` MUST NOT быть обычным результатом
разрешения packaged flow на поддерживаемой платформе.

#### Scenario: Промежуточный symlink
- **WHEN** любой component, ведущий к выбранному flow, является symbolic link
- **THEN** USW останавливается до чтения flow или вызова модели

#### Scenario: Packaged flow без descriptor-relative access
- **WHEN** packaged `<name>/FLOW.md` разрешается на поддерживаемой платформе без `dir_fd`
- **THEN** USW использует pathname-based backend и возвращает те же name, origin, identity, path, flow directory и точный Markdown, что и на остальных платформах

#### Scenario: Packaged resource без descriptor-relative access
- **WHEN** packaged Markdown называет sibling resource на такой платформе
- **THEN** resource читается через ту же boundary, привязывается к исходным flow identity и entrypoint и отклоняется при link, escape или неожиданном filesystem type
