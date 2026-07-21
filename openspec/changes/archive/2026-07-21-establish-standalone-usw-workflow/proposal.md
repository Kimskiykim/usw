## Why

Сейчас USW инициализирует workspace в форме OpenSpec и предоставляет набор
изолированных skills, но не определяет полноценный самостоятельный workflow,
устойчивое владение общими артефактами исполнения и явную оркестрацию. Из-за
этого OpenSpec фактически обязателен, а продолжение работы, планирование,
evidence и совместимость зависят от догадок агента.

## What Changes

- Добавить версионированную общую конфигурацию USW, которая выбирает provider
  артефактов и общий корень; standalone USW используется по умолчанию.
- Изменить инициализацию проекта: создавать самостоятельный USW workspace,
  только сообщать об уже существующем OpenSpec workspace и никогда не принимать
  или изменять его неявно.
- Добавить явные flow scenarios и оркестратор `usw-run-flow`, которые отвечают
  за порядок skills, ветвления, права записи и условия остановки.
- Определить три flow ответственности — Analysis, Development и Testing — на
  одном lifecycle с внутренними human review, transition review принимающей
  стороны, явным владением артефактами и возвратами к их владельцам.
- Требовать от Analysis оценки сложности спецификации до исполнимого
  планирования и предлагать декомпозицию только с подтверждением пользователя.
- При неоднозначном запросе на продолжение требовать от пользователя выбрать
  scope исполнения вместо применения неявного значения по умолчанию.
- Назначить один authoritative artifact для статуса change-задачи, устойчивого
  контракта и milestones задачи, раздельного Development/Testing evidence,
  reviewer-owned transition receipts и личной точки возобновления с журналом
  текущей сессии.
- Определить Delivery как терминальный per-run контракт, принятие которого не
  разрешает автоматически commit, push, pull request, deployment, release или
  другое внешнее действие.
- Добавить устойчивое пошаговое уточнение задачи: один decision case за ход и
  итог, пригодный для последующих planning flows.
- Добавить опциональную совместимость с OpenSpec через реальные integration
  tests: точная версия `1.6.0` блокирует release, а проверка latest остаётся
  видимой, но неблокирующей.
- **BREAKING** Изменить общий workspace по умолчанию с обязательных артефактов
  `openspec/` на самостоятельные USW-артефакты под `usw/`.

## Capabilities

### New Capabilities

- `workspace-configuration`: версионированная конфигурация provider/root и
  безопасная standalone-инициализация с неразрушающим обнаружением OpenSpec.
- `flow-orchestration`: общий lifecycle для Analysis, Development и Testing,
  включая выбор scope, права на артефакты, human review gates, возвраты к
  владельцам, терминальный Delivery и условия остановки.
- `execution-artifacts`: каноническое владение и lifecycle для task contract,
  milestone history, раздельного evidence, неизменяемых review receipts и
  локального состояния возобновления.
- `task-refinement`: устойчивое итеративное уточнение по одному decision case за
  ход с переиспользуемым согласованным итогом.
- `openspec-compatibility`: явный OpenSpec provider и проверяемый контракт
  совместимости и release gate.

### Modified Capabilities

Нет. В репозитории пока нет принятых основных capability specs.

## Impact

- Изменятся команды и templates инициализации, `usw-initialize-project` и их
  tests: безопасным значением по умолчанию станет standalone workspace.
- Появятся общая конфигурация, три role scenario, оркестрация, planning и
  execution artifacts, review receipts и capability-oriented skills.
- Существующие skills для handoff, planning и refinement будут согласованы с
  контрактами полномочий и оркестрации.
- Development и CI получат OpenSpec для compatibility tests, но standalone
  пользователям не потребуется OpenSpec как runtime dependency.
- README, packaging manifests, installers и архитектурная документация будут
  обновлены для двух поддерживаемых режимов workspace.
