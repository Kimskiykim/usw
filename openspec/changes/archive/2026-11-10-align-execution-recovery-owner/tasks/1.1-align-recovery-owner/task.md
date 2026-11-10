# Task 1.1: Согласовать recovery owner

## Artifact model

- `v1`

## Result

Pause и replanning одной text operation имеют один authoritative recovery
owner — exact operation document по `live-operation-state`; HANDOFF остаётся
router, а shared task/evidence/review artifacts сохраняют свои обязанности.

## Scope

Три requirement blocks delta `../../specs/execution-artifacts/spec.md` и их
sync в `openspec/specs/execution-artifacts/spec.md`;
`tests/test_execution_recovery_contract.py`;
`usw/backlog/AUD-T08.md` и строка/счётчик P2 `usw/BACKLOG.md`.
Main-spec/card/index edits должны быть сделаны до final product manifest.

## Non-scope

F04 и другие карточки, SKILL/commands/references, backend/runtime/CLI,
формат state, migration/install, commit/push/integration и закрытие goal.
Новая очередь, специальные model CLI/API inference, availability/effort
и before/after probes запрещены. Поведение любой модели не гарантируется.

## References

- `../../proposal.md`, `../../design.md`, delta выше.
- `openspec/specs/live-operation-state/spec.md`: Generic handoff и pause.
- `usw/backlog/AUD-T08.md`; исходное evidence:
  `usw/reviews/skills-prompts-audit-2026-10-03/DATA_AND_CONTRACTS.md`, T08.
- `openspec/context/06-testing-and-quality.md` и `08-process-conventions.md`.
- Actual roots, paths и baseline identities — design §§3–4, Context.

## Dependencies

Независимый planning review этой revision и отдельное поручение apply.
Перед apply сверить branch/HEAD/source и raw planning hashes с local freeze;
не использовать installed T01 или root checkout как source ветки.
Назначенный Development — единственный writer продукта; до передачи writer
не меняется. Любое расширение scope сначала возвращается человеку.

## Definition of done

Все три MODIFIED blocks применены целиком, пять исходных scenarios сохранены.
Pause position/next action и replanning pending actions принадлежат exact
operation document; HANDOFF не получает narrative recovery content.
Generic flow без OpenSpec tasks сохраняет narrative context без обязательных
artifact roles/evidence/receipts. `live-operation-state` остаётся нормативным
домом routed state, не дублируется новым форматом или протоколом.

Незатронутые нормы completion, contracts, legacy, evidence ownership/staleness,
source identity, review receipts и replanning history сохранены, включая
правила новой revision при stable-contract изменении и неизменной revision
при перестановке локальных действий. Вся artifact spec не объявлена архивной.
Адресный stable-token regression обнаруживает старое назначение owner.

Ordinary reader независимо прочитал итоговые specs и выбрал owner для трёх
случаев Verification; evidence содержит его фактический ответ и вывод проверки,
а не обещание будущего чтения. Специальные backend probes и model inference
не заменяют эту проверку.
Card AUD-T08 содержит проверяемую ссылку на change/результат, индекс удаляет
только её строку и корректирует P2 count. F04 и goal остаются открыты.

Все обязательные local checks успешны на конечном source. Development пишет
только `development-evidence.md`, Testing — только `testing-evidence.md` в этом
task directory. Immutable entries имеют ID, revision, source, фактический check,
result и timestamp; currentness сравнивает оба identities. Смена contract/source
делает всё прежнее evidence stale; перед повторным завершением полный набор
checks выполняется заново. До checkbox применимые operations завершены либо
их ошибка честно обработана. Checkbox означает только готовность Development,
а human/Testing/Delivery требуют своих gates и immutable receipts.

## Verification

1. Добавить адресный deterministic contract-test main-spec blocks:
   path/role anchors router и exact operation document для pause/replanning,
   ссылка `live-operation-state`, сохранность ключевых task/evidence/review
   anchors. Он должен выявлять исходный owner-конфликт, не фиксировать целые
   предложения. Сравнить остальные семь requirements и неизменные parts/scenarios
   трёх blocks с baseline; зафиксировать actual diff, потерь быть не должно.
2. Независимому ordinary reader дать итоговые specs и три ситуации без алгоритма
   автора: Development pause до завершения; перестановка pending локальных
   действий; pause generic flow без shared artifacts. Проверить, что он выбирает
   exact operation document для context/next action, HANDOFF только router,
   сохраняет подтверждённые факты и не создаёт shared artifacts/receipts ради
   handoff. Это проверка чтения конкретной редакции, не universal model proof.
3. Выполнить `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p test_execution_recovery_contract.py -v`,
   затем `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v`.
   Ожидание: exit 0. Новые temporary fixtures только с явным
   `tempfile.TemporaryDirectory(dir='/tmp')`; reports/proof — только под
   `.usw/state/run-handoff/align-execution-recovery-owner/` этой копии.
4. Выполнить `openspec validate align-execution-recovery-owner --strict`,
   `git diff --check`, v1 task validation; проверить один linked checkbox и
   отсутствие completion в leaf. Не сокращать MODIFIED ради length warning.
   `SKILL.md` не меняется, behavior evals и новый inference runner не требуются.
5. После main-spec/card/index edits вычислить полный `USW-SOURCE-V1` с actual
   exclusions design §3, записать commands/results/source в role-owned evidence;
   проверить raw planning hashes и stable digest отдельно. Независимые Testing
   и review receipts ссылаются на ту же revision/source и reviewed raw hashes.

Обязательные command entries Development evidence:

- Run: `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p test_execution_recovery_contract.py -v`
- Run: `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v`
- Run: `openspec validate align-execution-recovery-owner --strict`
- Run: `git diff --check`

## Contract revision

- `t08-c1`
- Stable identity: SHA-256 stable prefix до первого anchored
  `\n## Milestone log\n`, с `rstrip()` и одним конечным LF, как
  `task_contract_identity`; Milestone log исключён. Raw hash всего `task.md`
  фиксируется отдельно, включая log.

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
| --- | --- | --- | --- | --- | --- |
| — | Planning AUD-T08 на F05 baseline | `t08-c1` | Implementation не начата | Только план, исполнения и task evidence нет | Proposal, design, delta |
