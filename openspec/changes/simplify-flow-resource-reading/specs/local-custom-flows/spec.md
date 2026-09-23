## MODIFIED Requirements

### Requirement: Paths local flow остаются внутри безопасного local state
Система MUST отклонять local root, package directory или entrypoint,
которые выходят за пределы local state, проходят через symbolic link либо
имеют неожиданный filesystem type. Последующее чтение обычных файлов по
инструкции flow выполняется инструментами агента с их обычными границами;
USW не добавляет для таких файлов отдельную защиту или identity.

#### Scenario: Path local flow небезопасен
- **WHEN** `.usw`, `.usw/flows`, component package или выбранный entrypoint небезопасен
- **THEN** создание или execution останавливается до чтения, записи или вызова flow

#### Scenario: Локальный packaged flow читает соседний файл
- **WHEN** безопасно разрешённый local `FLOW.md` называет файл внутри своего каталога
- **THEN** исполнитель читает его обычным инструментом при необходимости, без повторного разрешения flow через USW

