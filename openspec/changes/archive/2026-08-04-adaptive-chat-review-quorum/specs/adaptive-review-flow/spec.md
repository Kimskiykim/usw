## ADDED Requirements

### Requirement: Review profile отделён от executor
Adaptive review flow SHALL передавать каждому reviewer-у отдельные `Scope`,
`Review focus` и `Output contract`, а выполнение одного ревью SHALL поручать
`usw-structured-review`. Named review profile SHALL разворачиваться в эти три
блока без подмены executor-а.

#### Scenario: Выбран LLM-critic profile
- **WHEN** flow получает review profile `llm-critic`
- **THEN** reviewer выполняет одно `usw-structured-review` с полным prompt
  `usw-reviewer-llm-critic` как review focus

#### Scenario: Profile неизвестен
- **WHEN** flow не может разрешить named review profile в непустые scope, focus
  и output contract
- **THEN** flow возвращает `decision_required` до запуска subagents

### Requirement: Review budget выбирается явно или по оценке
Flow SHALL принимать Markdown-параметр `--reviewers auto|2|3` внутри
пользовательского input; default SHALL быть `auto`. Значение `auto` SHALL
выбирать три reviewer-а при любом high-impact trigger либо минимум двух
uncertainty factors и два reviewer-а во всех остальных случаях.

High-impact triggers SHALL включать security/privacy, irreversible data,
public API или schema migration, concurrency и deployment. Uncertainty factors
SHALL включать multi-component scope, ambiguous requirements, weak or missing
tests/evidence и external integrations.

#### Scenario: Низкорисковый локальный scope
- **WHEN** `--reviewers auto` не обнаруживает high-impact trigger и обнаруживает
  меньше двух uncertainty factors
- **THEN** основной агент выбирает двух reviewer-ов и сообщает краткую причину

#### Scenario: Высокий impact
- **WHEN** `--reviewers auto` обнаруживает хотя бы один high-impact trigger
- **THEN** основной агент выбирает трёх reviewer-ов и сообщает trigger

#### Scenario: Накопленная неопределённость
- **WHEN** `--reviewers auto` обнаруживает минимум два uncertainty factors
- **THEN** основной агент выбирает трёх reviewer-ов и перечисляет factors

#### Scenario: Явный budget
- **WHEN** пользователь передаёт `--reviewers 2` или `--reviewers 3`
- **THEN** flow использует указанное начальное число reviewer-ов и фиксирует,
  что выбор был ручным

#### Scenario: Неверный параметр
- **WHEN** значение `--reviewers` отсутствует после имени, повторено или не
  равно `auto`, `2` либо `3`
- **THEN** flow возвращает `decision_required` до запуска subagents

### Requirement: Findings проходят явное bounded majority vote
Reviewers SHALL сначала независимо найти candidates. Основной агент SHALL
дедуплицировать candidates, назначить им стабильные в пределах запуска IDs и
получить от каждого активного reviewer-а явный `support`, `reject` или
`abstain` по каждому candidate. Отсутствие candidate в первоначальном отчёте
MUST NOT считаться `reject`.

#### Scenario: Два reviewer-а согласны
- **WHEN** два reviewer-а дают одинаковый non-abstain vote по candidate
- **THEN** flow фиксирует решение `2/2` без запуска третьего reviewer-а

#### Scenario: Два reviewer-а расходятся
- **WHEN** после двух reviewer-ов candidate не получил двух одинаковых
  non-abstain votes
- **THEN** flow запускает ровно одного третьего reviewer-а только для
  неразрешённых candidates

#### Scenario: Три reviewer-а дают большинство
- **WHEN** candidate получает минимум два `support` или минимум два `reject`
  среди трёх reviewer-ов
- **THEN** flow фиксирует соответствующий majority verdict `2/3` или `3/3`

#### Scenario: После трёх reviewer-ов большинства нет
- **WHEN** abstentions или расхождения не дают двух одинаковых non-abstain votes
- **THEN** flow не запускает четвёртого reviewer-а и возвращает
  `decision_required` с evidence и vote provenance

### Requirement: Человек принимает решение по каждому finding
После majority vote flow SHALL показать evidence, provenance и рекомендацию по
каждому candidate и SHALL получить отдельное human decision
`fix-finding` либо `reject-finding`. Majority verdict SHALL быть рекомендацией,
а не заменой human decision.

#### Scenario: Пользователь принимает часть findings
- **WHEN** пользователь выбирает `fix-finding` для одних IDs и
  `reject-finding` для других
- **THEN** flow сохраняет оба множества без требования общего решения для всего
  review

#### Scenario: Решение дано не для всех findings
- **WHEN** хотя бы один candidate не получил human decision
- **THEN** flow возвращает `decision_required` только для оставшихся IDs

#### Scenario: Findings отсутствуют
- **WHEN** после review и voting нет material findings
- **THEN** flow завершает review как `accept-as-is` без implementation actions

### Requirement: Review-to-fix handoff остаётся read-only
Завершённый flow SHALL вернуть accepted findings, rejected findings, evidence,
vote provenance и рекомендуемый отдельный implementation flow. Review flow
MUST NOT менять reviewed files, автоматически запускать implementation или
получать новые permission boundaries.

#### Scenario: Есть findings для исправления
- **WHEN** хотя бы один finding получил `fix-finding`
- **THEN** output содержит bounded implementation scope только для этих IDs

#### Scenario: Finding отклонён
- **WHEN** finding получил `reject-finding`
- **THEN** он остаётся в review outcome с решением и не входит в
  implementation scope
