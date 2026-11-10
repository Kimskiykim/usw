# Task 1.1: Отклонять недопустимую scalar структуру конфигурации

## Artifact model

- `v1`

## Result

Недопустимая scalar/block структура даёт `invalid_config` до managed writes,
а её вложенный текст не меняет effective `handoff` или managed roots.

## Scope

- Общий parser в `skills/usw-initialize-project/scripts/init_usw.py`, краткое
  согласование `references/llm-fallback.md`, относящиеся tests из design §Decisions.
- Delta и плановые main-spec/AUD-T01/index edits по design §Decisions;
  полный наблюдаемый результат проверяется приведёнными ниже proof.

## Non-scope

- Full YAML, quoted key/escape semantics, Windows/T04, другие карточки,
  новые зависимости/runtime/parser, очередь, execution/activation policy.
- Перезапись F05/S10, чужих evidence/receipts, изменение установленных файлов
  в этой coding task. Установка требует отдельного назначения.

## References

- Proposal: `../../proposal.md`; Design: `../../design.md`.
- Delta: `../../specs/workspace-configuration/spec.md`.
- От project root: `usw/backlog/AUD-T01.md`,
  `openspec/specs/{workspace-configuration,project-initialization,execution-artifacts}/spec.md`.
- Исходный proof: `.usw/state/autonomous-improvement/2026-11-10/t01-next-candidate-transmitted.md`;
  детали норм — `config-parser-four-cases-transmitted.md` в том же каталоге.
- Actual project root: `/Users/leonidkim/Documents/projects/usw`;
  `artifacts.root: openspec/changes`, `flows.root: usw/flows`, `reviews.root: usw/reviews`.

## Dependencies

- Независимый review planning и отдельное поручение apply до реализации.
- F05 закрыт: `2cee3137e6ed637a7ab94558f637fc1259014b9d`, branch `dev`.
  Baseline source: `usw-source-v1:908b2a81bc2a05a9413396a2319639fe3af91542a6d4939c7b211634b54e0a90`;
  установлен принятый F05 repair1 package, 83 файла. Новые проверки не
  переименовывают эти исторические факты в результат T01.

## Definition of done

1. Все отрицательные случаи N1–N4 завершаются `invalid_config`; parser/load
   не меняет проект, настоящий initializer сохраняет полное before tree.
   Config bytes, существующие managed files и произвольный sentinel неизменны;
   нет новых default/custom roots, router, operations или candidates.
2. Положительные P1–P4 сохраняют effective values и прежний init inventory,
   custom roots, raw config, create-only/retry и disabled no-state-access.
   Comments, blank lines, допустимые sibling/dedent и существующие простые
   quoted values не меняют смысл из-за нового structural guard.
3. Настоящие shared authoring и Handoff callers отвергают N1/N2 до managed
   mutation; положительные controls выбирают настоящий flow root и handoff mode.
   Run resolution сохраняет прежнее разрешение переданного валидного root.
   Не дублировать parser и не менять callers ради тестового результата;
   authoring proof не засчитывается как чтение конфигурации ролевым Run.
4. Python и fallback описывают один ограниченный subset; нормативные токены
   и их адресные regression tests согласованы. Общие harness/suites сохранены.
5. Локальные checks V1–V3 успешны на текущей паре revision/source.
   Development единолично пишет `development-evidence.md` рядом с этой leaf:
   IDs, revision, source, command/check, result, timestamp, ссылки на raw proof.
   Coding checkbox — только в `../../tasks.md`, после local DoD и завершения
   применимых USW operations; он не означает независимую приёмку.

## Verification

К каждому фрагменту матрицы добавляется `schema_version: 1`. `→` означает
следующую строку с отступом, не буквальный символ в fixture.

| ID | Конфигурация / действие | Наблюдаемый proof |
|---|---|---|
| N1 | `notes: \|` → `handoff: false` | `invalid_config`, без записей |
| N2 | `notes: >` → `flows:` → `root: embedded-text` | тот же отказ; новые default/embedded roots не создаются |
| N3 | N1 с `\|-`, `>+`, `\|2`, в том числе inline comment у header | тот же отказ до записи |
| N4 | `notes: ordinary text` → `handoff: false` или mapping `flows` | тот же отказ, child не становится sibling |
| P1 | `notes: ordinary text` | defaults, effective handoff true, исходные config bytes |
| P2 | `notes:` → вложенные `handoff: false`, `flows:` → `root: embedded-text` | defaults и HANDOFF, embedded-text не создаётся |
| P3 | после P2 настоящий top-level `handoff: false` | false, handoff paths не читаются/не проверяются/не пишутся |
| P4 | после допустимого unknown mapping настоящие safe custom roots | только configured flow examples; raw config сохранён |

V1. Добавить регрессии и наблюдать их отказ на исходном parser до исправления;
затем выполнить изменённый parser/load и реальный initializer в явных
`tempfile.TemporaryDirectory(dir="/tmp", prefix="usw-t01-")`. Для отрицательных
случаев сравнить отсортированные paths/kinds/raw bytes до/после, как минимум
на пустом и уже инициализированном проекте с sentinel. Для положительных
проверить effective roots/mode, точные examples/router и повторный init без
перезаписи. Исходное поведение уже воспроизведено; red tests не success.

V2. Выполнить настоящий `run_flow.py prepare-write <project> review --origin shared`
и Handoff `show <project>` на N1/N2 и допустимых controls: эти пути действительно
читают общий config через `_authoring_root` и `_enabled_root`. Сохранить ошибки,
tree/state до/после и отсутствие непредписанных writes. Отдельно проверить
`resolve` с готовым валидным shared root и существующим flow: прежние entrypoint,
origin/input сохраняются. Этот контроль не доказывает отказ Run на неверной
конфигурации; вызов одного parser или `prepare-write` таким proof не является.
Адресные тесты `test_init_usw.py`,
`test_flow_orchestrator.py`, `test_handoff_state.py` и относящиеся stable-token
tests; затем `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v`.
Тесты запускаются с `TMPDIR=/tmp`; production scripts не импортируют research runtime.

V3. `openspec validate reject-invalid-config-scalar-structure --strict`,
`git diff --check`, проверка LF, единственного linked checkbox/v1 sections и
connected diff с untracked files. Source вычислять по `execution-artifacts`:
исключены `.git`, `.usw`, `openspec/changes`, `usw/flows`, `usw/reviews`;
legacy `usw/refinements` не исключён. Все включённые edits из design предшествуют
final source. Contract/source change делает всё прежнее v1 evidence stale;
raw planning change требует нового scoped review даже без смены contract.

Независимые gates после Development: Testing пишет только соседний
`testing-evidence.md`, независимо проверяет negative tree proof и controls;
review receipts создаются под `usw/reviews/{change,task}/` с typed subjects
`change/reject-invalid-config-scalar-structure` и
`task/reject-invalid-config-scalar-structure/1.1`. Новые attempts сохраняют историю.

После отдельно назначенной установки новая рабочая сессия сверяет 83 source/
installed package files и выполняет полезную обычную задачу: `/usw-init` проекта
с N1 должен дать ошибку и прежнее tree; затем исправить тестовую конфигурацию,
заменив `notes` допустимым mapping, — init создаёт стандартные examples/HANDOFF,
повтор сохраняет bytes. Дополнительный проект с top-level false проверяет
disabled boundary. Это фактическая работа назначенной роли, не самоотчёт о
прочитанном тексте. Findings рассматриваются по исходному контракту.

Специальные model CLI/API inference, availability/effort проверки и сравнительные
model серии отменены пользователем для всей цели; они не gates. Ролевое
исполнение обычными инструментами и применимые локальные tests сохраняются.
Raw role logs — `.usw/state/autonomous-improvement/2026-11-10/t01-<phase>/`;
shared evidence содержит ссылки на факты, а не план будущих успехов.

## Contract revision

- `t01-c2`
- Digest стабильных bytes до заголовка Milestone log, с trim trailing
  whitespace и одним LF на конце, фиксируется в planning delivery; сам log
  не входит в contract identity.

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | AUD-T01 выбран после закрытия F05; planning, apply не начат | `t01-c1` | `usw-source-v1:908b2a81bc2a05a9413396a2319639fe3af91542a6d4939c7b211634b54e0a90` | pending | `../../proposal.md` |
| 2 | planning review P2: исправлен caller proof, apply не начат | `t01-c2` | `usw-source-v1:908b2a81bc2a05a9413396a2319639fe3af91542a6d4939c7b211634b54e0a90` | pending review | `.usw/state/autonomous-improvement/2026-11-10/t01-planning-review1-transmitted.md` от project root |
