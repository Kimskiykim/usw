## ADDED Requirements

### Requirement: Недопустимая scalar структура отклоняется до записи
Чтение `usw.yaml` SHALL завершаться `invalid_config` до managed writes при
неподдерживаемом block scalar или вложенном mapping под scalar. Некавычечные
заголовки `|` и `>` с модификаторами также MUST отклоняться. Отступ MUST
сохранять принадлежность поддерживаемых mapping: вложенный текст MUST NOT
становиться управляющими ключами родительского mapping.

#### Scenario: Block scalar содержит handoff
- **WHEN** неизвестное поле `notes: |` содержит вложенный `handoff: false`
- **THEN** конфигурация отклоняется с `invalid_config`, существующие bytes
  сохраняются и managed artifacts не создаются

#### Scenario: Block scalar содержит flow root
- **WHEN** неизвестное поле с literal или folded block scalar содержит
  вложенные `flows:` и `root: embedded-text`
- **THEN** конфигурация отклоняется до записи в default или указанный в тексте root

#### Scenario: Обычный scalar получает дочерний mapping
- **WHEN** после `notes: ordinary text` следует более глубоко вложенный
  `handoff: false` либо `flows:` с `root`
- **THEN** чтение завершается `invalid_config` до managed writes

#### Scenario: Shared authoring и Handoff читают недопустимую структуру
- **WHEN** shared authoring разрешает configured flow root либо Handoff проверяет capability
  по конфигурации с такой недопустимой scalar структурой
- **THEN** caller сообщает ошибку конфигурации и не выполняет managed mutation

### Requirement: Допустимые неизвестные поля инертны
USW SHALL игнорировать неизвестные поля, синтаксически допустимые в
поддерживаемом mapping/scalar subset v1, сохраняя исходный `usw.yaml`
byte-for-byte. Эти поля MUST NOT менять managed roots или effective `handoff`.

#### Scenario: Неизвестные scalar и mapping сохранены
- **WHEN** конфигурация содержит обычный неизвестный scalar либо неизвестный
  mapping с вложенными именами `handoff` и `flows`
- **THEN** применяются только действительные настройки v1, а содержимое
  неизвестного поля не влияет на managed artifacts

#### Scenario: Известное поле следует после неизвестного mapping
- **WHEN** после допустимого неизвестного mapping отступ возвращается к
  top-level `handoff: false` или поддерживаемому custom root
- **THEN** эта действительная настройка применяется по прежнему контракту
