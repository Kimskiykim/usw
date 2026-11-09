# Спецификация flow-assessment

## Purpose
Определяет явно выбранный read-only semantic assessment безопасно разрешённых
USW Markdown flows, включая structured verdicts, анализ dependencies и
завершимости, воспроизводимое evidence и консервативные границы non-execution.

## Requirements

### Requirement: Assessment выбирается явно и остаётся read-only
USW SHALL предоставлять
`$usw-assess-flow [--local|-l|--shared] <flow-name> [<scenario-input>]` только
по явному запросу пользователя. Он MUST NOT создавать, обновлять, исполнять или исправлять
flow, читать или изменять HANDOFF, execution state либо product files. Только
leading tokens до safe name SHALL считаться origin selectors; недопустимые
комбинации SHALL возвращать `insufficient-data`, а trailing text SHALL
оставаться opaque scenario input.

#### Scenario: У assessment нет origin selector
- **WHEN** пользователь передаёт одно safe flow name и optional scenario input
- **THEN** USW оценивает сначала local, затем shared, не исполняя flow

#### Scenario: У assessment конфликтующие selectors
- **WHEN** перед flow name одновременно указаны `--local` и `--shared`
- **THEN** USW возвращает `insufficient-data` до чтения flow

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

### Requirement: Assessment возвращает structured semantic verdict
USW SHALL возвращать один verdict: `executable`, `executable-with-risks`,
`not-executable` или `insufficient-data`. Report SHALL идентифицировать flow,
кратко описывать terminal paths, перечислять dependencies и давать каждому
существенному finding локальный для вызова ID, severity `blocking|risk`, type,
точное evidence, impact и минимальное исправление Markdown. Доказанный blocking
defect SHALL давать `not-executable`; иначе недостаточная semantics SHALL давать
`insufficient-data`, существенные risks — `executable-with-risks`, а связный flow
без существенных findings — `executable`.

#### Scenario: Связный конечный flow
- **WHEN** обязательные steps и dependencies достигают объявленных outcomes без
  существенного риска
- **THEN** report возвращает `executable` без findings

#### Scenario: Проза не позволяет построить path
- **WHEN** текст не поддерживает связное следующее действие или terminal
  interpretation
- **THEN** report возвращает `insufficient-data` и указывает недостающую semantics

### Requirement: Assessment обнаруживает логические дефекты и дефекты завершимости
USW SHALL проверять reachability, outcomes веток и ошибок, необходимые данные,
противоречащие действия, явные markers `LOOP` и неявные возвраты. Для каждого
достижимого цикла он SHALL оценивать exit, конечный bound или escalation,
наблюдаемый progress и повторяемые необратимые side effects. Безусловный цикл
без выхода и небезопасный необратимый repeat SHALL быть blocking; неопределённый
eventual exit SHALL быть risk; bounded cycle с terminal fallback SHALL NOT быть
blocking. Однократный approval вне loop SHALL NOT делать безопасным необратимое
действие внутри loop. Без idempotency guarantee и действие, и его approval SHALL
оставаться вне loop.

#### Scenario: Два раздела возвращаются друг к другу бесконечно
- **WHEN** A достигает B, а B безусловно возвращается к A без выхода
- **THEN** report возвращает `not-executable` с blocking finding о цикле

#### Scenario: Retry имеет конечный fallback
- **WHEN** число попыток ограничено, а исчерпание возвращает `failed` или
  `decision_required`
- **THEN** loop не создаёт blocking finding о незавершимости

#### Scenario: Exit зависит от eventual success
- **WHEN** flow повторяет действие до успеха без bound или escalation
- **THEN** report записывает risk, а не утверждает бесконечный цикл

#### Scenario: Необратимое действие повторяется
- **WHEN** достижимый цикл может повторить необратимое действие без idempotency
  guarantee
- **THEN** report возвращает blocking finding `unsafe-repeat`

#### Scenario: Approval предшествует небезопасному repeat
- **WHEN** один approval находится перед loop, способным повторить необратимое
  действие
- **THEN** report всё равно возвращает blocking finding `unsafe-repeat`

### Requirement: Результаты dependency analysis сохраняют неопределённость
USW SHALL проверять объявленные dependencies и именованные вызовы skill, command
или flow без их исполнения. Каждая dependency SHALL иметь status `confirmed`,
`missing` или `unverified`; первые два требуют authoritative evidence. Доступные
contracts SHALL проверяться на обязательные inputs и retired selectors, но child
flows MUST NOT проходить recursive assessment. Отсутствующая mandatory dependency
без handling SHALL быть blocking; явное terminal handling SHALL не позволять
одному отсутствию стать blocking. Доказанный contract-invalid mandatory
invocation, включая отсутствующий required input или retired selector, без
обработанного terminal fallback SHALL быть blocking reachable dead end, даже
если сама dependency подтверждена.

#### Scenario: Mandatory dependency отсутствует без handling
- **WHEN** authoritative lookup доказывает отсутствие, а fallback или terminal
  response не предусмотрены
- **THEN** report возвращает blocking dependency finding

#### Scenario: Отсутствующая dependency ведёт к решению
- **WHEN** недоступность явно возвращает `decision_required`
- **THEN** отсутствие отражается в report, но само по себе не является blocking

#### Scenario: Mandatory invocation нарушает подтверждённый contract
- **WHEN** обязательный call использует доказанный retired selector и не имеет
  terminal fallback
- **THEN** report возвращает `not-executable` с blocking finding о reachable dead end

### Requirement: Semantic acceptance evidence воспроизводимо
USW SHALL хранить fixture Markdown и raw reports, использованные для semantic
acceptance checks, внутри change. Acceptance summaries SHALL различать expected
mappings и фактически наблюдавшиеся reports и указывать invocation boundary.
Если assessment skill не исполнялся, summary MUST помечать mappings как
expected-only и MUST NOT заявлять наблюдавшееся semantic behavior.

#### Scenario: Semantic smoke указан как observed
- **WHEN** acceptance evidence помечает verdict как observed
- **THEN** соответствующие checked-in fixture и raw assessment report указывают,
  как был получен verdict

### Requirement: Optional scenario создаёт subordinate trace
При наличии scenario input USW SHALL хранить его отдельно от immutable Markdown
и трассировать вероятные steps, gates и stop или ambiguity. Trace MUST NOT
ослаблять findings на других объявленных paths.

#### Scenario: Scenario выбирает одну здоровую ветку
- **WHEN** scenario завершается, но другая объявленная ветка является blocking
- **THEN** trace завершается, а общий verdict сохраняет finding

### Requirement: Assessment не даёт machine guarantee
USW SHALL описывать результат как semantic model analysis и MUST NOT заявлять
parser-backed proof, deterministic transition graph, persistent cursor,
recursive validation или execution authority.

#### Scenario: Report представлен
- **WHEN** assessment возвращает любой verdict
- **THEN** он указывает, что результат является evidence-backed semantic
  analysis, а не machine guarantee

### Requirement: Обычная прямая просьба активирует оценку flow
Прямая просьба оценить или проверить именно flow SHALL считаться явным запросом
без обязательного имени skill или команды. Простое упоминание flow и общая
проверка кода MUST NOT активировать assessor. Неоднозначный объект SHALL
уточняться до загрузки flow; оценка MUST NOT давать разрешение на запуск или правки.

#### Scenario: Просьба обычными словами
- **WHEN** пользователь просит «оцени flow test-evidence»
- **THEN** assessor извлекает однозначное безопасное имя и выполняет read-only
  оценку по действующим правилам selector и scenario input

#### Scenario: Flow только упомянут
- **WHEN** пользователь обсуждает сроки существующего flow либо просит проверить код
- **THEN** assessor не активируется без прямой просьбы оценить именно flow

#### Scenario: Объект оценки неоднозначен
- **WHEN** пользователь просит оценить flow, а однозначное имя не дано и
  не определяется из контекста
- **THEN** агент спрашивает, какой flow требуется, до inspect или чтения entrypoint

#### Scenario: Объект уже выбран в контексте
- **WHEN** запрос «оцени этот flow» однозначно относится к ранее выбранному safe name
- **THEN** assessor использует этот объект, не требуя повторного вызова по имени skill
