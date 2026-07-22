## 1. Experimental structured parser

- [x] 1.1 Добавить version-aware data model и сохранить parser версии 1
- [x] 1.2 Разобрать typed calls, постоянные имена и subagent payload version-2
- [x] 1.3 Разобрать и проверить GATE, LOOP и PARALLEL control blocks

## 2. Experimental runtime orchestration

- [x] 2.1 Разрешать exact typed executors и передавать invocation payload
- [x] 2.2 Исполнять gate transitions и bounded loop state по одной boundary
- [x] 2.3 Исполнять PARALLEL после полного preflight и агрегировать outcomes
- [x] 2.4 Сохранять и восстанавливать version-2 cursor и loop counters

## 3. Default Markdown facade

- [x] 3.1 Удалить незавершённый binding, требующий готовый action-specific input map
- [x] 3.2 Принять общую задачу и безопасное имя flow без требования версии
- [x] 3.3 Искать flow по deterministic local → shared resolution и сообщать origin
- [x] 3.4 Передавать задачу и исходный Markdown generic executor без strict parsing
- [x] 3.5 Фиксировать default run как одну HANDOFF begin/outcome boundary

## 4. Experimental opt-in

- [x] 4.1 Перенести автоматический выбор v1/v2 parser за `--experimental-structured`
- [x] 4.2 Не включать strict runtime только по metadata документа
- [x] 4.3 Сохранить typed calls, gates, loops, parallel и cursor в opt-in path
- [x] 4.4 Сделать именованные inputs/results необязательной experimental возможностью

## 5. Skill contracts and documentation

- [x] 5.1 Обновить `usw-run-flow` вокруг default-контракта «задача + flow name»
- [x] 5.2 Закрепить structured creation только за явным режимом `usw-create-flow`
- [x] 5.3 Обновить references, README и примеры без обязательного version-2 DSL

## 6. Verification

- [x] 6.1 Покрыть plain Markdown, versioned Markdown без opt-in и local → shared lookup
- [x] 6.2 Покрыть explicit experimental mode и отсутствие обязательного action map
- [x] 6.3 Проверить HANDOFF, permissions и отсутствие переписывания source flow
- [x] 6.4 Запустить `python3 -m unittest discover -s tests`
- [x] 6.5 Запустить `openspec validate add-structured-flow-runtime --strict`
