# Исполнение structured flow version-2

Использовать этот reference только после того, как validator выбрал точную
версию `version-2`.

## Executable-поднабор

Принимать только каноническую форму, которую понимает validator:

- верхнеуровневые действия последовательно пронумерованы и имеют глобально
  уникальные постоянные kebab-case имена;
- typed call записан как `CALL SKILL`, `CALL SCRIPT`, `CALL FLOW`,
  `CALL SUBAGENT` или `CALL HUMAN` с точной целью в backticks;
- literal arguments script записаны отдельной строкой `Аргументы`;
- `GATE` содержит конечные outcomes, по одному полному `IF`/`ELIF` route на
  outcome и `ELSE`;
- `LOOP` содержит положительный предел, существующий gate, один call на
  попытку, возврат к gate и явный exhaustion outcome;
- `PARALLEL` содержит не менее двух именованных child calls;
- каждый `CALL SUBAGENT` содержит непустой вложенный нумерованный payload.

Не интерпретировать другое расположение keyword или похожий prose. `MODEL`,
произвольные jumps, неполные gates и unbounded loops отклонять до Begin.

## Typed executors

- `CALL SKILL`: вызвать capability по точному имени с текущим scope.
- `CALL SCRIPT`: повторно проверить project-relative regular executable без
  symlink, получить отдельное разрешение на точный путь и передать literal argv
  без shell.
- `CALL HUMAN`: обратиться к указанному человеку или роли. Для `GATE` принять
  только один объявленный outcome; иной ответ применяет `ELSE` и возвращает
  `decision_required` без перехода.
- `CALL FLOW`: передать точное имя flow adapter того же выбранного origin/root.
  Adapter валидирует child, не допускает cycle по ancestor identities и
  возвращает parent outcome только после terminal outcome child flow.
- `CALL SUBAGENT`: создать субагента указанной роли и передать ему один payload,
  содержащий parent flow identity, имя parent action, scope и вложенные действия
  в исходном порядке. В prompt явно потребовать выполнить только этот payload,
  вызывать каждый вложенный skill/flow по точному имени и вернуть единый
  structured outcome. Не разворачивать nested actions в parent cursor и не
  отправлять skill отдельным несвязанным сообщением.

Composite executor обязан агрегировать свои actual writes, references и
verification. Parent cursor продвигается только после его `completed`.

## Control cursor

После completed обычного action перейти к следующему верхнеуровневому имени.
После completed `GATE` перейти только к target его exact outcome. Неизвестный
outcome оставляет cursor на gate и возвращает `decision_required`.

После completed loop attempt увеличить счётчик этого постоянного имени и
вернуться к объявленному gate. Если gate снова направляет в loop при счётчике,
равном пределу, не вызывать executor: вернуть `loop_exhausted` с текстом поля
`При исчерпании`.

Для `PARALLEL` сначала разрешить всех children. Затем запустить их одновременно,
дождаться всех outcomes и агрегировать writes/references в порядке документа.
Любой non-completed outcome останавливает весь block; следующий top-level
action недоступен.

## HANDOFF и возврат

Begin сохраняет exact flow origin/identity, scope, постоянное имя boundary и
loop counters. Outcome записывается до изменения cursor. Resume с другой
identity, origin или source context считается stale; `in_progress` не
перезапускается автоматически.

После одной parent boundary вернуть управление пользователю. Commit, push, PR,
deployment и release по-прежнему требуют отдельного явного разрешения.
