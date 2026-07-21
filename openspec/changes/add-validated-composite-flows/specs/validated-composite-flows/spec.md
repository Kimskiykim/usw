## ADDED Requirements

### Requirement: Именованный project-owned flow
Система SHALL принимать явное имя flow, разрешать его как безопасное имя файла
под настроенным `flows.root` и загружать только соответствующий project-owned
Markdown-файл без packaged runtime fallback.

#### Scenario: Успешное разрешение имени
- **WHEN** пользователь запускает `usw-run-flow` с существующим безопасным именем
- **THEN** система загружает `<flows.root>/<name>.md`

#### Scenario: Небезопасное или отсутствующее имя
- **WHEN** имя содержит path traversal, абсолютный путь, symlink escape либо соответствующий файл отсутствует
- **THEN** система останавливается до исполнения с наблюдаемой ошибкой разрешения flow

### Requirement: Минимальный Markdown-контракт
Система SHALL валидировать обычный Markdown-документ с версией контракта,
упорядоченными действиями и полномочиями записи. Остальной Markdown SHALL
считаться документацией и SHALL NOT влиять на исполнение.

#### Scenario: Валидный документ
- **WHEN** Markdown содержит поддерживаемую версию, действия и полномочия записи
- **THEN** система создаёт валидированное внутреннее представление flow до исполнения

#### Scenario: Невалидный документ
- **WHEN** обязательное поле отсутствует, повторено, имеет неподдерживаемую форму или неизвестную версию
- **THEN** система сообщает точное место и причину ошибки без запуска шагов

### Requirement: Линейные типизированные шаги
Каждый пункт последовательности SHALL иметь ровно один тип: установленный skill
или project-local script. Номер пункта SHALL определять его позицию и resume
index. Flow SHALL NOT поддерживать branches, циклы или иной выбор следующего
шага.

#### Scenario: Последовательное выполнение
- **WHEN** текущий шаг завершился со статусом `completed`
- **THEN** следующим доступным шагом становится непосредственно следующий пункт списка

#### Scenario: Попытка описать переход
- **WHEN** flow содержит branch, обратный переход, loop или иной произвольный target
- **THEN** валидация отклоняет документ до исполнения

### Requirement: Разрешение skill
Шаг skill SHALL ссылаться на доступный skill по точному имени. Система SHALL
сопоставить capability contract skill с входами и полномочиями flow до вызова и
SHALL NOT заменять отсутствующий skill похожей capability.

#### Scenario: Skill доступен и разрешён
- **WHEN** указанный skill доступен, а его permitted writes входят в полномочия flow
- **THEN** система вызывает skill один раз с контекстом текущего шага

#### Scenario: Skill отсутствует
- **WHEN** указанный skill невозможно разрешить
- **THEN** flow останавливается до mutation со статусом `blocked`

### Requirement: Безопасный project-local script
Шаг script SHALL указывать безопасный project-relative путь к существующему
regular file и отдельный список аргументов. Система SHALL NOT принимать shell-
строку, выполнять command substitution или разрешать путь вне project root.

#### Scenario: Разрешённый script
- **WHEN** путь проходит проверку, аргументы структурированы и требуемое разрешение предоставлено
- **THEN** система запускает ровно этот script без shell-интерпретации

#### Scenario: Небезопасный script
- **WHEN** путь выходит из project root, проходит через symlink, либо команда задана shell-строкой
- **THEN** система отклоняет шаг до запуска

### Requirement: Единый результат и остановка
Каждый шаг SHALL возвращать нормализованный status, outcome, written roles и
output references. Система SHALL переходить к следующему шагу только после
`completed`; `failed`, `blocked`, `decision_required` и permission boundary
SHALL останавливать flow с одной следующей безопасной операцией.

#### Scenario: Успешный шаг
- **WHEN** шаг возвращает `completed` и не нарушает контракт writes
- **THEN** система сохраняет его references и разрешает следующий шаг

#### Scenario: Шаг требует остановки
- **WHEN** шаг возвращает любой неуспешный или требующий решения status
- **THEN** система не запускает последующие шаги и сообщает причину остановки

### Requirement: Проверка полномочий
Система SHALL сравнить declared writes каждого шага с полномочиями flow до
mutation и SHALL проверить фактически сообщённые writes после шага. Delivery,
commit, push, pull request, deployment и release SHALL по-прежнему требовать
отдельного явного разрешения пользователя.

#### Scenario: Несовпадение полномочий до шага
- **WHEN** declared writes шага не входят в полномочия flow
- **THEN** система останавливается до вызова executor

#### Scenario: Нарушение контракта executor
- **WHEN** завершившийся шаг сообщает writes вне объявленных полномочий
- **THEN** система помечает запуск failed и не продолжает flow

### Requirement: Возобновление с незавершённого шага
Система SHALL сохранять имя flow, identity его контракта, выбранный scope и
индекс следующего незавершённого шага в developer-local checkpoint. Resume
SHALL продолжать только если контракт flow и применимый source context не стали
stale.

#### Scenario: Безопасное продолжение
- **WHEN** checkpoint fresh и ранее завершённые шаги соответствуют текущему flow identity
- **THEN** система продолжает с первого незавершённого шага

#### Scenario: Flow изменился после остановки
- **WHEN** identity Markdown flow не совпадает с сохранённой
- **THEN** система не продолжает автоматически и требует нового scoped run

### Requirement: Существующие role flows не изменяются
Добавление custom flows SHALL NOT менять формат, lookup или исполнение packaged
Analysis, Development и Testing scenarios.

#### Scenario: Запуск существующего role flow
- **WHEN** пользователь запускает существующий role flow
- **THEN** система сохраняет прежнее поведение без миграции его Markdown-файла
