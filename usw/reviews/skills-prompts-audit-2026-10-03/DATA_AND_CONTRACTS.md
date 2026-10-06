**Третий этап аудита USW: данные, контракты и композиция ролей**

4 октября 2026. Ревизия `db38d99`. AgentMiracle и три субагента. Продолжение [основного разбора](/Users/leonidkim/Documents/projects/usw/usw/reviews/skills-prompts-audit-2026-10-03/REVIEW.md) и [аудита записи, восстановления и установки](/Users/leonidkim/Documents/projects/usw/usw/reviews/skills-prompts-audit-2026-10-03/SECONDARY_AUDITS.md).

Найдены **8 новых проблем P2**: шесть воспроизведены на данных во временных проектах, две подтверждены сопоставлением текстовых контрактов. Отдельно указаны условный риск композиции и неточность описания тестового охвата. Исправления не применялись.

Основной вывод: следующие улучшения должны укрепить границы преобразования данных. Частичный YAML parser не должен молча менять смысл настроек; валидированный документ операции должен безопасно преобразовываться в router; результат роли должен содержать данные, которые требует следующий этап.

**T01 · P2 · Текст неизвестного YAML-поля становится управляющими настройками**

Место: [init_usw.py:108](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/scripts/init_usw.py:108). Парсер не сохраняет границу scalar и не запрещает вложенную mapping под ним. Для следующего документа он считает `flows` полем верхнего уровня:

```yaml
schema_version: 1
notes: |
  flows:
    root: embedded-text
```

Наблюдалось: `flow_root='embedded-text'`, initializer создаёт `embedded-text/examples/chat-review.md`. Вариант `notes: |` с вложенной строкой `handoff: false` отключает HANDOFF. Неверный отступ после обычного scalar также принимается как верхнеуровневый ключ. Неизвестные поля должны быть инертны — это прямо сказано в [fallback:25](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/references/llm-fallback.md:25).

Исправление: проверять структуру отступов; не разрешать дочерние mapping под scalar. Неподдержанный block scalar явно отклонять до записи либо сохранять как непрозрачное значение неизвестного поля. Критерий: содержимое заметки не влияет на `flows.root`/`handoff`; некорректный отступ не превращается в другую конфигурацию. Новый универсальный YAML-парсер для этого не обязателен.

**T02 · P2 · Кавычки вокруг ключа отключают его смысл и проверку дубликатов**

Места: [чтение ключа:108](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/scripts/init_usw.py:108), [проверка provider:157](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/scripts/init_usw.py:157), [handoff:163](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/scripts/init_usw.py:163).

Кавычки остаются частью имени. Наблюдалось: `"handoff": false` создаёт HANDOFF с effective `true`; ключ `"provider": legacy` внутри секции `artifacts` проходит вместо отказа; `"root": intended` внутри `flows` выбирает default root. Одновременные `handoff: true` и `"handoff": false` не считаются дубликатом.

Исправление: нормализовать поддерживаемые quoted keys до поиска полей и проверки дубликатов. Неподдерживаемую форму ключа явно отклонять, а не превращать известное поле в неизвестное. Критерий: четыре описанных случая соблюдают явную настройку или дают ошибку до записи; [запрет provider](/Users/leonidkim/Documents/projects/usw/openspec/specs/workspace-configuration/spec.md:28) не обходится кавычками. Полная поддержка YAML не требуется, но граница допустимого синтаксиса должна быть явной.

**T03 · P2 · Quoted scalar записывается в каталог с другим именем**

Место: [init_usw.py:123](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/scripts/init_usw.py:123). Парсер только снимает крайние кавычки, не декодируя их содержимое и не проверяя закрытие.

| Значение `flows.root` в файле | Смысл YAML | Наблюдавшийся root после полной инициализации |
| --- | --- | --- |
| `'team''s flows'` | `team's flows` | `team''s flows` |
| `"team\u0020flows"` | `team flows` | `team/u0020flows` |
| `"unfinished` | Незакрытая строка, ошибка | Каталог с буквальным первым символом `"` |

Во втором случае последующая нормализация обратной косой черты дополнительно превращает escape в разделитель пути. Quoted roots уже поддерживаются существующим [тестом:27](/Users/leonidkim/Documents/projects/usw/tests/test_init_usw.py:27), поэтому простое отсутствие общей YAML-библиотеки не объясняет молчаливую другую семантику.

Исправление: декодировать заявленные quoted scalars; неизвестные escapes и незакрытые кавычки отклонять до записи. Критерий: точное имя каталога для поддерживаемого значения; отсутствие изменений для неподдерживаемого. Документировать малое допустимое подмножество и применять его одинаково в Python и LLM fallback.

**T04 · P2 · Валидатор относительных roots принимает Windows drive paths**

Место: [init_usw.py:183](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/scripts/init_usw.py:183). После замены разделителей проверяется `PurePosixPath`, который не распознаёт drive-qualified пути.

`C:\outside\flows` успешно принят как `C:/outside/flows`; `C:flows` тоже принят. Полная инициализация на macOS создала соответствующие буквальные каталоги внутри временного проекта. `PureWindowsPath('D:/workspace') / 'C:/outside/flows'` даёт путь другого диска, а `C:flows` сохраняет drive-relative семантику. Это не project-relative roots по [spec:41](/Users/leonidkim/Documents/projects/usw/openspec/specs/workspace-configuration/spec.md:41).

Исправление: отклонять drive-qualified формы до нормализации, включая `C:relative`. Критерий: drive-absolute, drive-relative и UNC отклоняются; допустимый `usw\flows` работает. **Запись вне проекта на Windows не доказана:** native Windows не запускалась, поздние проверки конкретного writer могут остановить такой путь. Находка относится к общему валидатору.

**T05 · P2 · Unicode-разделители строк ломают сохранение exact input**

Места: [сериализация Input:887](/Users/leonidkim/Documents/projects/usw/skills/usw-manage-handoff/scripts/handoff_state.py:887), [разбор строк:747](/Users/leonidkim/Documents/projects/usw/skills/usw-manage-handoff/scripts/handoff_state.py:747).

Для пользовательского ввода `First\u2028second`, где `\u2028` обозначает настоящий Unicode-символ, `render_begin` возвращает `invalid_handoff: Input must be one JSON string`. То же происходит с U+0085 и U+2029. `ensure_ascii=False` оставляет символ буквально; `splitlines()` разделяет JSON, а сборка секций заменяет его на недопустимый внутри JSON-строки LF. Корректный непустой input не доходит до исполнения при включённом handoff. Аналогичные символы в workspace hints дают `invalid_workspace`.

Исправление: экранировать структурно опасные Unicode-разделители в JSON-полях, например через `ensure_ascii=True`, сохраняя точное декодированное значение и digest. Критерий: Begin → read → decoded input/digest совпадают для всех трёх символов; workspace либо сохраняет допустимое значение, либо явно отклоняет его до сериализации. Обычные LF/CRLF, кавычки, backslash и Markdown headings внутри input уже прошли адресную проверку.

**T06 · P2 · Принятая парсером дата позволяет Show записать невалидный router**

Места: [timestamp validator:339](/Users/leonidkim/Documents/projects/usw/skills/usw-manage-handoff/scripts/handoff_state.py:339), [вставка даты в таблицу:559](/Users/leonidkim/Documents/projects/usw/skills/usw-manage-handoff/scripts/handoff_state.py:559), [запись при discovery:1163](/Users/leonidkim/Documents/projects/usw/skills/usw-manage-handoff/scripts/handoff_state.py:1163).

Во временном документе операции Updated заменён на ``2026-10-04`00:00:00+00:00``. `parse_handoff` принимает его: `datetime.fromisoformat` допускает такой разделитель. `discover_handoffs` заменяет корректный router строкой с лишней обратной кавычкой, затем возвращает `invalid_router`; последующее чтение по exact operation ID тоже получает `invalid_router`. Ни mocks, ни гонка, ни I/O-отказ не требуются.

Штатный `_timestamp` такого значения не создаёт: условие — изменённый или импортированный документ. Само обновление видимой таблицы при Show разрешено контрактом; проблема в публикации невалидного результата. Исправление: сузить принимаемую форму timestamp и проверять подготовленный router до replace. Критерий: неподдерживаемая дата отклоняется, байты router и документов операций сохранены.

**T07 · P2 · Custom discovery может не предоставить данные для обязательного voting**

Места: [custom preflight:55](/Users/leonidkim/Documents/projects/usw/usw/flows/chat-review.md:55), [объединение findings:116](/Users/leonidkim/Documents/projects/usw/usw/flows/chat-review.md:116), [candidate ledger:129](/Users/leonidkim/Documents/projects/usw/usw/flows/chat-review.md:129). Те же инструкции находятся в поставляемых копиях примера.

Статический сценарий: custom profile задаёт проверку безопасности и `Output contract: вернуть только число дефектов`. Он проходит проверку непустоты; ответ `2` соблюдает контракт, но не содержит двух findings, evidence и областей исправления. Следующие обязательные этапы выполнить по нему нельзя. Проверка «ответ соответствует output contract» эту несовместимость не обнаруживает.

Исправление: установить минимальный смысл custom результата — отдельные findings с evidence либо явный clean/incomplete outcome. Оформление и фокус могут быть пользовательскими; несовместимость выявлять до запуска reviewers. Критерий: count-only/общий PASS-FAIL требуют уточнения контракта, полноценный список и явный clean result проходят. Flow и модели не запускались; фактический ложный `accept-as-is` не утверждается. Интерфейс команды критика расширять для этого не требуется.

**T08 · P2 · Две действующие спецификации назначают разные места recovery state**

[execution-artifacts:25](/Users/leonidkim/Documents/projects/usw/openspec/specs/execution-artifacts/spec.md:25) требует записывать текущую операцию и next action в `.usw/HANDOFF.md`; [replanning:175](/Users/leonidkim/Documents/projects/usw/openspec/specs/execution-artifacts/spec.md:175) также помещает туда pending операции. Однако [live-operation-state:9](/Users/leonidkim/Documents/projects/usw/openspec/specs/live-operation-state/spec.md:9) определяет HANDOFF как router, а [pause:35](/Users/leonidkim/Documents/projects/usw/openspec/specs/live-operation-state/spec.md:35) направляет recovery content в точный operation document.

Это подтверждённый конфликт нормативных текстов. Следование старому месту записи может привести к несовместимому документу, но фактическая порча router из этих инструкций не воспроизводилась. Исправление: точечно заменить владельца recovery content в execution-artifacts ссылкой на routed operation contract. Не объявлять всю спецификацию архивной и не удалять правила evidence/receipts без отдельного решения. Критерий: обе спецификации направляют pause/replanning одной операции в один authoritative документ, сохраняя разделение router и operation state.

**Условный риск композиции, отдельно от восьми находок**

[Рецепт конвейера:72](/Users/leonidkim/Documents/projects/usw/skills/usw-create-flow/references/recipes/subagent-orchestration.md:72) передаёт reviewer только `evidence.md`. Если эту роль выполняет `usw-reviewer-llm-critic` без отдельного Scope, [его правило:16](/Users/leonidkim/Documents/projects/usw/commands/usw-reviewer-llm-critic.md:16) делает аргумент областью ревью, а findings за её пределами запрещены. Тогда корректно оформленный отчёт о проверках можно проверить, не имея права публиковать дефект связанного кода, и ошибочно использовать этот результат как одобрение реализации.

Рецепт не назначает именно этого критика, поэтому это риск конкретной композиции. Улучшение примера: «Reviewer получает исходную цель и критерии, Scope изменённого кода, проверяемую Version; evidence передать как Inputs». Проверка будущего flow: отчёт о проверках оформлен корректно, но реализация содержит заданный дефект; reviewer должен оценивать разрешённую область реализации.

**Неточность описания тестового охвата · P3**

[Research README:17](/Users/leonidkim/Documents/projects/usw/research/structured-runtime/README.md:17) говорит, что содержимое research не входит в main test discovery. Но [test_artifact_contract.py:10](/Users/leonidkim/Documents/projects/usw/tests/test_artifact_contract.py:10) и [test_replanning.py:12](/Users/leonidkim/Documents/projects/usw/tests/test_replanning.py:12) импортируют оттуда `artifact_contract.py`: соответственно 10 и 6 тестов.

Поэтому ранее пройденные 275 тестов включали 16 проверок исторического artifact helper. Это не означает запуск старого structured executor и не доказывает наличие этого helper в установленной поставке. Исправление описания: назвать оставшуюся роль helper в тестах; отдельно решить, нужен ли он как тестовый эталон поддерживаемых templates/contracts. Не удалять проверки ради согласования с неточным README. Уточнение внесено в основной отчёт аудита.

**Проверки, исключения и порядок работы**

Прочитаны parser/config boundary, сериализация handoff, пять команд ролей и их основные композиции, связанные текущие specs и открытые changes. Root независимо повторил ключевые T01–T06, сверил T07 с полным flow, T08 дополнительно подтвердил субагент. Все записи выполнялись в автоматически удаляемых временных проектах. Общая suite, живые модели, установка и удалённые CI на этом этапе не запускались; исходники остались прежними.

Итоговый текст сверили два субагента. Для T04 отдельно проверена полнота доказательства: субагент инициализировал drive-absolute вариант, а root дополнительно выполнил полную инициализацию и для `C:flows`; оба наблюдения относятся только к macOS. Остальные выводы и ограничения подтверждены без существенных поправок.

Не посчитаны заново: поиск по описанию уже запланирован в `add-flow-skill-frontmatter`; раннее завершение refine-intent без вопросов уже отмечено в основном отчёте; неизвестные статусы веток и incomplete aggregation — тоже прежние предложения. Ограничение assessment без рекурсивного чтения child flow является явным контрактом, а не случайно пропущенной возможностью.

Сначала исправить T01–T04 как четыре узкие проверки parser/validator с отдельными наблюдаемыми исходами. Затем T05/T06: точное сохранение ввода и проверка router до публикации. T07 и T08 — отдельные изменения контрактов с адресными сценариями. Для T07 нужны безопасные stub-ответы ролей и последующий opt-in behavior eval; статическая правка сама по себе не доказывает поведение модели.
