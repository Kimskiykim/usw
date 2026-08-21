# Спецификация normative-text-structure

## Purpose
Определяет единый нормативный слой USW, структуру производных skill-инструкций,
язык нормативных текстов и требования к безопасной реструктуризации.

## Requirements

### Requirement: Один нормативный источник
USW SHALL хранить ровно одну нормативную формулировку каждого правила. Этим
источником является `openspec/specs/`. README SHALL быть обзором со ссылками на
него, а skill files SHALL быть производными инструкциями для executor, а не
второй specification. Правило, сформулированное более чем в одном месте, MUST
быть сведено к одной формулировке, а остальные места должны ссылаться на неё.

#### Scenario: Правило изменяется
- **WHEN** нормативное правило добавляется или меняется
- **THEN** оно редактируется ровно в одном file, а другие files не повторяют его
  в форме, способной разойтись

#### Scenario: Читателю нужна authoritative формулировка
- **WHEN** documentation и skill выглядят противоречащими друг другу
- **THEN** specification является authoritative, а skill исправляется в
  соответствии с ней

### Requirement: Skill files начинаются с imperative
Каждый поставляемый skill SHALL сначала кратко и в imperative form указывать,
что делать. Обоснования, edge cases, recipes и worked examples SHALL находиться
в `references/` и читаться по необходимости. Skill file MUST NOT требовать,
чтобы читатель усвоил предшествующую стену оговорок до основной инструкции.

#### Scenario: Executor читает skill
- **WHEN** модель вызывает skill
- **THEN** обязательные действия сформулированы до их обоснования

#### Scenario: Правилу нужно длинное обоснование
- **WHEN** для понимания правила требуется подробное объяснение
- **THEN** объяснение переносится в `references/`, а в skill остаётся само правило

### Requirement: Смысл защищается измерением, а не phrase assertions
Тесты instruction text SHALL проверять только anchors, стабильные по своей
природе: command names, error codes, file paths и structural markers. Test MUST
NOT проверять наличие конкретного предложения, потому что это закрепляет wording
и мешает делать текст яснее. Invariants поведения модели SHALL вместо этого
покрываться behavior scenarios. Phrase assertion MUST NOT удаляться до появления
scenario, покрывающего тот же invariant.

#### Scenario: Wording улучшается без изменения смысла
- **WHEN** instruction переписана короче с сохранением смысла
- **THEN** deterministic suite продолжает проходить

#### Scenario: Invariant теряет phrase assertion
- **WHEN** phrase-level assertion удаляется
- **THEN** до этого существует behavior scenario, покрывающий тот же invariant

### Requirement: Нормативный слой использует один язык
Нормативные bodies skills, specifications и README SHALL быть русскими. Один
file MUST NOT смешивать языки внутри нормативного body. Установленные technical
terms, command names, error codes и identifiers остаются в исходной форме.
Frontmatter fields `description` являются metadata harness, а не нормативным
body, и не входят в scope.

#### Scenario: Обнаружен skill на другом языке
- **WHEN** body поставляемого skill написано не по-русски
- **THEN** оно переводится с сохранением command names, error codes и identifiers

#### Scenario: Правилу нужен technical term
- **WHEN** правило ссылается на command, error code или identifier
- **THEN** token сохраняет исходную форму, а не переводится

### Requirement: Реструктуризация не меняет behavior
Эта реструктуризация SHALL сохранять каждое переносимое правило. Различие
behavior, наблюдаемое во время работы, является defect, который нужно исправить,
а не improvement, который можно оставить. Behavior scenarios SHALL измеряться
до и после, а падение rate MUST быть исследовано до продолжения change.

#### Scenario: Text реструктурирован
- **WHEN** skill переписывается в рамках этого change
- **THEN** его наблюдаемые scenario rates измеряются до и после и приводятся
  вместе
