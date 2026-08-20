# Модель routed state (usw-manage-handoff)

Читать при вопросах об устройстве router и operation documents, миграциях и
конкурентных переходах. Для обычных вызовов команд этот файл не нужен:
SKILL.md самодостаточен.

## Router и operation document

`.usw/HANDOFF.md` — validated Markdown router: таблица от каждой registered
exact operation identity к одному generated relative path под
`.usw/handoffs/`. Членство в router определяет, зарегистрирована ли operation;
сам operation document остаётся authoritative для её mutable status и recovery
context. Таблица — единственное представление routes: скрытого второго списка
нет, и для каждой строки видны summary, flow, status, Started, Updated и
ссылка на operation. Exact operation ID восстанавливается из validated path.

`Workspace` в operation document хранит Git base revision, наблюдённую в
Begin (или явные `unborn`, `not-git`, `unknown`), bounded expected-write hints
и фактически reported changed areas последнего Outcome. Эти сведения нужны
только для recovery: они не предоставляют write authority, не доказывают
ownership и не обнаруживают пересечения между concurrent operations.
`Current position` — narrative text, не machine cursor.

## Identity и сериализация

Operation ID выводится из unique invocation token, origin, flow identity и
SHA-256 exact input; validated hex suffix определяет имя файла. Router entry,
запрошенный ID и embedded identity документа обязаны совпадать при каждом
доступе, а декодированный exact input — совпадать со своим digest.

Begin, Outcome, Save, Finish и Cleanup сериализуют полный read-check-write
переход под общим коротким project-local lock. Begin сначала создаёт и
подтверждает `in_progress` operation document, затем добавляет exact ID в
router с readback и только потом возвращает ID и path. Outcome обновляет
только выбранный authoritative document и затем освежает human-readable
snapshot в router. Finish сначала подтверждённо удаляет route, затем только её
document и candidate; cleanup failure после unregistration может оставить
безопасный orphan, но не возвращает operation в recovery. Cleanup сначала
подтверждает новый router без terminal routes, затем удаляет только их
documents и candidates.

## Миграции и совместимость

Generic single-state HANDOFF мигрирует под lock: idle превращается в empty
router; non-idle сначала exact-byte записывается в operation document по его
validated embedded identity и только потом HANDOFF заменяется router-ом —
до успешной замены single-state файл остаётся authoritative. Legacy role-based
HANDOFF доступен только для Show/Resume/Finish, блокирует Begin и не
мигрируется автоматически; его Finish создаёт empty router.

Старые generic operation documents без Summary, Started и Workspace читаются
без изменения байт; discovery выводит bounded summary из exact input и
показывает unknown start time. Outcome такого документа записывает enriched
форму с явными `unknown` для недоступных исторических полей. Enriched
operation нельзя заменить старой формой; старую generic operation разрешено
обновить только enriched candidate с `Started: unknown`, unknown base и
пустыми expected writes.
