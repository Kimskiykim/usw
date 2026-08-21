# Cookbook: context packs

Status: draft

Context pack — компактная карта одной предметной области проекта. Она помогает
человеку или следующему агенту быстро найти действующие contracts, точки входа,
инварианты и проверки, не перечитывая весь репозиторий.

Пакет не заменяет исходный код, тесты и project docs и не становится новым
source of truth. Это проверяемый индекс к первичным источникам на указанном
baseline. При расхождении всегда заново исследовать актуальные источники.

## Когда создавать пакет

Создать context pack, когда хотя бы одно условие выполняется:

- работа затрагивает несколько компонентов одной предметной области;
- один и тот же domain приходится заново исследовать для аудита, incident,
  handoff, review или следующего change;
- знания о поведении разбросаны между кодом, tests, configuration и docs;
- изменение пересекает внешнюю границу: API, storage, queue, CLI, plugin,
  process boundary или другой subsystem;
- неверное понимание invariant или touchpoint заметно повышает риск работы.

Не создавать пакет для тривиальной локальной правки, если boundary и contract
уже очевидны из одного небольшого файла и его tests. Пакет не должен быть
церемонией ради полноты документации.

## 1. Выбрать domain boundary

1. Назвать capability или поведение, которое нужно понять, а не просто
   директорию: например, «разрешение Markdown flow», а не «папка scripts».
2. Найти входы в domain: public functions, commands, handlers, jobs, config keys
   и форматы данных.
3. Проследить прямые callers, callees и data flow до мест, где меняется contract
   или ownership.
4. Включить собственный код domain, его tests, fixtures, configuration и
   нормативную документацию.
5. Соседние системы описать как touchpoints. Не втягивать их реализацию внутрь
   boundary без необходимости.
6. Исключить unrelated code, generated/vendor artifacts, caches, binaries и
   секреты. Не копировать чувствительные runtime values в пакет.
7. Если возможны несколько разумных границ, выбрать наименьшую, которая
   полностью объясняет нужное поведение, и записать альтернативы в open
   questions.

Boundary должен отвечать на три вопроса:

- что принадлежит этому domain;
- с чем он взаимодействует через явную границу;
- что намеренно не исследовано.

## 2. Исследовать первичные источники

Использовать источники в порядке их близости к текущему поведению:

1. актуальный собственный код: entry points, data models, state transitions,
   error paths и configuration reads;
2. tests и fixtures, которые наблюдаемо фиксируют contracts и edge cases;
3. interface definitions: schemas, protocol docs, CLI help, manifests и config
   examples;
4. нормативные project docs и применимые `AGENTS.md`;
5. доступные runtime observations: logs, traces, metrics или incident evidence с
   известной датой и environment;
6. Git history — только для подтверждения причины решения или его изменения;
7. issues, TODO, roadmap и OpenSpec changes — только как intent, lead или
   материал для дедупликации, не как доказательство текущего поведения.

При конфликте источников не выбирать удобный вариант. Записать расхождение,
проверить текущий код и tests и оставить unresolved часть в open questions.
Не называть inference фактом только потому, что она правдоподобна.

## 3. Зафиксировать пакет

Рецепт не требует единого storage path. Использовать принятый в проекте tracked
docs root либо developer-local место для временного пакета. В любом случае
сделать location явным и не смешивать context pack с normative specification.

Начать со следующего шаблона и удалить неприменимые пустые строки:

```markdown
# Context pack: <domain>

Status: draft | peer-checked | stale
Audience: <для кого и для какой работы>
Captured at: <ISO date/time и timezone>
Baseline: <commit/ref + clean/dirty state либо другой воспроизводимый identity>

## Purpose and boundary

Purpose: <какое повторяющееся исследование заменяет этот пакет>
In scope:
- <capability/path/symbol>

Out of scope:
- <соседняя область и причина исключения>

## Touchpoints

| Direction | Touchpoint | Contract | Evidence |
| --- | --- | --- | --- |
| inbound/outbound | `<path:symbol>` | <что входит/выходит> | <source ref> |

## Invariants

| Invariant | Evidence | Consequence if broken |
| --- | --- | --- |
| <проверяемое утверждение> | <source/test ref> | <наблюдаемый эффект> |

## Tests and checks

| Behavior | Test or command | Last verified | Result/source |
| --- | --- | --- | --- |
| <contract> | `<test path>` или `<command>` | <baseline/date/not run> | <pass/fail/unknown + evidence> |

## Sources and freshness

| Source | Why primary | Observed at | Freshness |
| --- | --- | --- | --- |
| `<path:symbol>` | <что подтверждает> | <baseline/date> | current/stale/unknown |

## Open questions

- Q1: <что пока неизвестно> — owner/evidence needed: <кто или что подтвердит>

## Peer-check

Reviewer: pending | <person/agent>
Checked against baseline: <identity>
Verdict: pending | passed | needs-refresh
Notes: <что независимо подтверждено или не совпало>

## Refresh log

- <date/baseline>: created | refreshed | marked stale — <что изменилось>
```

### Purpose and boundary

Purpose описывает полезность пакета одной фразой: какую повторяющуюся работу он
сокращает и какое решение помогает принять. Boundary перечисляет конкретные
capabilities, paths или symbols и явные exclusions. Не использовать «всё рядом»
или имя большой директории без объяснения.

### Touchpoints

Для каждой границы записать направление, обе стороны, передаваемые данные,
ошибки и ownership contract. Ссылка должна вести к актуальному symbol, schema,
test или нормативному документу. Touchpoint — это граница взаимодействия, а не
полный пересказ соседней системы.

### Invariants

Invariant должен быть проверяемым утверждением о действующем поведении.
Например: «local flow выбирается раньше shared при одинаковом safe name».
Каждый invariant получает первичный source и наблюдаемое последствие нарушения.
Если подтверждения нет, перенести утверждение в open questions.

### Tests and checks

Связать важное поведение с test path или документированной командой. Не писать
`passes`, если проверка не запускалась на указанном baseline. В таком случае
использовать `not run` или `unknown` и сослаться на последнее доступное evidence
с его датой. Не запускать потенциально записывающую или внешнюю проверку только
ради заполнения таблицы без обычного разрешения пользователя.

### Sources and freshness

Для каждого существенного вывода указать source, baseline или дату наблюдения и
freshness: `current`, `stale` либо `unknown`. Runtime evidence дополнительно
получает environment и временное окно. Источник без воспроизводимого identity
не называть свежим.

Разделять три типа записей:

- **Fact** — прямо подтверждён текущим source или наблюдением;
- **Inference** — логический вывод с перечисленными фактами и альтернативами;
- **Open question** — нужное подтверждение пока отсутствует.

Inference не становится fact из-за повторения в нескольких context packs.

## Стабильные ссылки вместо слепых line numbers

- Основная ссылка: repository-relative path + symbol, heading, test name, config
  key или другой устойчивый anchor.
- Line number можно добавить только как навигационную подсказку вместе с
  baseline и устойчивым anchor.
- Не хранить голый `file:line` как единственное evidence: строки смещаются после
  любого редактирования.
- При refresh заново разрешить anchors и удалить либо обновить устаревшие line
  hints.
- Не копировать большие фрагменты кода. Короткая цитата допустима только для
  идентификации contract и не заменяет ссылку на source.

## 4. Провести независимый peer-check

Пакет остаётся `draft`, пока другой человек или агент независимо не проверит
его по актуальным первичным источникам. Reviewer не должен доверять самому
пакету как evidence.

Reviewer проверяет:

1. boundary охватывает заявленный purpose и не поглощает соседние domains;
2. критические touchpoints и invariants подтверждаются cited sources;
3. test claims соответствуют указанному baseline и фактическим результатам;
4. inference и open questions не замаскированы под facts;
5. sources имеют достаточную freshness, а line hints не являются единственными
   ссылками;
6. secrets, случайные runtime values и неподтверждённые выводы отсутствуют.

Записать reviewer, проверенный baseline, verdict и конкретные расхождения.
`passed` позволяет поставить `Status: peer-checked`. `needs-refresh` оставляет
пакет `draft` или переводит существующий пакет в `stale`. Peer-check не исправляет
код и не принимает продуктовые решения автоматически.

## 5. Обновлять после изменений

Обновить context pack, если изменилось хотя бы одно из следующего:

- included source, public contract, config key или data format;
- touchpoint, invariant, failure mode или ownership boundary;
- связанный test, fixture или documented check;
- ответ на open question;
- baseline, относительно которого пакет будет использоваться для нового
  решения.

При обновлении:

1. повторно прочитать затронутые первичные источники;
2. обновить baseline, freshness и только связанные sections;
3. заново разрешить symbols/headings и проверить optional line hints;
4. переместить опровергнутые inference в refresh log, не оставляя их facts;
5. добавить одну запись в refresh log;
6. повторить независимый peer-check для material boundary, touchpoint или
   invariant changes.

Если обновить пакет сейчас нельзя, поставить `Status: stale`, указать причину и
не использовать его как основание решения без повторного исследования кода.

## Связь с аудитом улучшений

При запуске [code-improvement-audit](../flows/code-improvement-audit.md) context
pack может ускорить выбор domain boundary и поиск первичных источников. Сам
пакет остаётся lead: аудит обязан заново проверить findings по текущему коду,
tests и baseline и не использовать сохранённые выводы как самостоятельное
evidence.

## Критерий готовности

Context pack готов к повторному использованию, когда:

- purpose и boundary конкретны;
- основные touchpoints, invariants и tests покрыты ссылками на первичные
  источники;
- у sources указаны baseline/freshness;
- неподтверждённое отделено в inference или open questions;
- peer-check выполнен на том же baseline;
- пакет не содержит secrets и не зависит от голых line numbers.

Готовый пакет сокращает discovery, но не отменяет проверку изменившихся или
критичных источников перед новым решением.
