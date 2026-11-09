**Дополнительные аудиты USW: запись, восстановление, установка, измерения**

3–4 октября 2026. Ревизия `db38d99`. AgentMiracle и три субагента. Продолжение [основного разбора скиллов и промптов](/Users/leonidkim/Documents/projects/usw/usw/reviews/skills-prompts-audit-2026-10-03/REVIEW.md); старые F/E-находки повторно не считаются.

Подтверждены **14 новых находок: 2 P1 и 12 P2**. Главные — потеря recovery state после частично успешной миграции HANDOFF и запись через descriptor каталога, который уже перемещён за пределы проекта. Каждая находка ниже имеет наблюдавшийся результат, узкое предложение и регрессионную проверку. Код USW не изменялся.

**Охват и условия**

| Направление | Что проверено | Кто проверял |
| --- | --- | --- |
| Доступ и восстановление | `safe_access.py`, `init_usw.py`, lifecycle/parser/error paths `handoff_state.py`, профильные specs/tests | `review_audit_evidence` |
| Flow loader и writer | `run_flow.py`: resolution, identity/token, staging, recheck, cleanup, readback, CLI | `audit_execution` |
| Установка и поставка | `install.sh`, manifests/marketplace metadata, история поставляемых компонентов, CI, package/platform tests | `audit_prompts` |
| Измерение поведения | `evals/run_evals.py`, сценарии, runner/error/transcript contract и tests | AgentMiracle |

Эксперименты выполнялись во временных каталогах. Сбои записи и конкурентные изменения вносились в заданной точке, после чего работал штатный код. Это проверки обработки отказов, а не наблюдения настоящего отключения питания или атаки. Реальные пользовательские установки, состояние `.usw` проекта, сеть и модели не затрагивались.

AgentMiracle независимо повторил S01, основной вариант S02, S05, оба буквальных input из S08, S09, S13 и S14; проверил историю S12. Для остальных использованы воспроизведения субагентов и сверка соответствующего кода. Нативная платформа — текущая macOS; ограничения симуляции Windows указаны в S06.

Итоговый текст дополнительно проверили два субагента: `audit_execution` и `review_audit_evidence`. Существенных поправок после сверки с кодом и воспроизведениями не потребовалось; подтверждены границы выводов, отсутствие повторного учёта старых F/E и арифметика тестов.

Приоритеты: P1 — исправить прежде, чем полагаться на затронутую операцию; P2 — следующий пакет надёжности. Они оценивают последствия при названных условиях, а не частоту возникновения.

**S01 · P1 · Миграция HANDOFF теряет состояние при ошибке после замены router**

Места: [атомарная запись:911](/Users/leonidkim/Documents/projects/usw/skills/usw-manage-handoff/scripts/handoff_state.py:911), [cleanup миграции:1048](/Users/leonidkim/Documents/projects/usw/skills/usw-manage-handoff/scripts/handoff_state.py:1048), [cleanup Begin:1275](/Users/leonidkim/Documents/projects/usw/skills/usw-manage-handoff/scripts/handoff_state.py:1275).

Миграция сначала создаёт документ операции, затем заменяет старый generic HANDOFF на router. Ошибка последующего `sync` попадает в обработчик, который удаляет созданный документ. Старого HANDOFF уже нет, новый router ссылается на отсутствующую операцию. Аналогичный обработчик Begin оставляет повреждённый маршрут.

Воспроизведение: после реального `replace` вызвать `OSError` из `DescriptorDirectory.sync` для `.usw`. Наблюдалось `router routes: 1`, `operation exists: False`, повторное чтение — `missing_operation`. При миграции утрачены исходные recovery facts. Это отдельный дефект данных; прежняя F05 относится к неверному обещанию статуса в инструкции.

Исправление: различать ошибку до замены и неподтверждённый результат после неё. Удалять новый документ только при подтверждённом отсутствии его маршрута; при неопределённости сохранять. Проверка: инъекции отказа `sync` и readback после реальной замены для migration и Begin; любой опубликованный маршрут разрешается в сохранённый документ. [Существующий тест:313](/Users/leonidkim/Documents/projects/usw/tests/test_handoff_state.py:313) подменяет всю `_atomic_write` и не достигает опасной границы.

**S02 · P1 · Writer не различает прежний и подставленный обычный каталог**

Места: [проверка parent:643](/Users/leonidkim/Documents/projects/usw/skills/usw-run-flow/scripts/run_flow.py:643), [удаление созданного каталога:580](/Users/leonidkim/Documents/projects/usw/skills/usw-run-flow/scripts/run_flow.py:580).

Повторная проверка открывает актуальный parent по пути, но не сравнивает его identity с ранее открытым descriptor, через который выполняется запись. После staging, до финальной проверки, пакет перемещён из проекта в соседний каталог; на прежнем месте создан другой обычный пакет. Результат: актуальный `FLOW.md` остался `Replacement`, перемещённый за пределы проекта получил `New`; только readback вернул `write_unverified`, `written: true`.

Вариант cleanup: новый пакет после создания перемещён, на его месте создан чужой пустой каталог, staging завершается ошибкой. Cleanup удаляет чужой каталог, а исходный созданный каталог остаётся. Запись воспроизведена на descriptor backend; неправильная очистка — также на принудительно выбранном pathname backend.

Исправление: сравнивать identity актуального parent и удерживаемого handle перед записью; при cleanup проверять identity именно созданного объекта. Проверка: подмена обычным каталогом во время staging останавливает замену, чужой каталог остаётся, внешний файл неизменен. Остаточное окно после последнего recheck здесь не рассматривается: оно явно исключено [design:32](/Users/leonidkim/Documents/projects/usw/openspec/changes/add-deterministic-flow-write/design.md:32), а подмена во время staging должна обнаруживаться по [design:174](/Users/leonidkim/Documents/projects/usw/openspec/changes/add-deterministic-flow-write/design.md:174).

**S03 · P2 · Частичный migration document блокирует автоматический повтор**

Места: [установка документа:954](/Users/leonidkim/Documents/projects/usw/skills/usw-manage-handoff/scripts/handoff_state.py:954), [cleanup:977](/Users/leonidkim/Documents/projects/usw/skills/usw-manage-handoff/scripts/handoff_state.py:977), [exclusive writer:141](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/scripts/safe_access.py:141).

Обработка очистки начинается после успешного `write_exclusive`. Если writer успел создать файл и выбросил ошибку внутри записи/flush, неполный документ остаётся. В эксперименте записаны `# De`, затем вызван `OSError`. Исходный generic HANDOFF сохранён; повтор миграции читает существующий неполный `<operation>.md` и каждый раз возвращает `invalid_handoff`.

Исправление: очищать принадлежащий текущей попытке неполный файл при ошибке exclusive creation, не трогая ранее существовавший destination. Проверка: partial write → исходник неизменен, неполного документа нет → повтор успешен. Уже существующий чужой файл должен сохраняться. Аналогичный [тест initializer:193](/Users/leonidkim/Documents/projects/usw/tests/test_init_usw.py:193) этот путь handoff не покрывает.

**S04 · P2 · Initializer после проверки parent записывает через подменённую ссылку**

Места: [parent preflight:302](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/scripts/init_usw.py:302), [create_file:334](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/scripts/init_usw.py:334).

`create_file` проверяет компоненты, затем снова открывает полный pathname. `O_NOFOLLOW` защищает последний компонент, но не родителя. Во время полного `initialize_usw` каталог `.usw` после проверки заменён ссылкой на соседний tempfile-каталог: снаружи проекта создан `.gitignore` с `*\n`; отказ обнаружен лишь на следующем файле.

Исправление: использовать существующую общую safe-access boundary и закреплённые handles для создания файлов и каталогов. Это уже предусмотрено [cross-platform-safe-access:31](/Users/leonidkim/Documents/projects/usw/openspec/specs/cross-platform-safe-access/spec.md:31). Проверка: подмена parent после preflight на POSIX не создаёт внешний файл. Более слабое окно pathname backend должно оставаться явно описанным ограничением.

**S05 · P2 · Регистр имени обходит запрет записи в `.git`**

Места: [сравнение roots:191](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/scripts/init_usw.py:191), [reserved roots:217](/Users/leonidkim/Documents/projects/usw/skills/usw-initialize-project/scripts/init_usw.py:217).

Сравнение строк чувствительно к регистру, текущий том macOS — нет. Без mocks: в tempfile создан обычный каталог `.git`, установлен `flows.root: .GiT`, initializer завершился успешно и создал `.git/examples/chat-review.md`. Нарушено требование отклонять пересечения с `.git` и `.usw` из [workspace-configuration:49](/Users/leonidkim/Documents/projects/usw/openspec/specs/workspace-configuration/spec.md:49).

Исправление: учитывать identity/aliases существующих каталогов и варианты регистра зарезервированных имён; согласовать с проверкой пересечений writable roots. Одного `os.path.normcase` на macOS недостаточно. Проверка на filesystem без различения регистра: `.GiT`, `.USW`, flow/review roots, различающиеся только регистром, отклоняются до изменений. Утверждение не распространяется на каждый macOS-том: filesystem может различать регистр.

**S06 · P2 · Pathname lock открывает заранее существующую ссылку**

Место: [handoff_state.py:186](/Users/leonidkim/Documents/projects/usw/skills/usw-manage-handoff/scripts/handoff_state.py:186).

`.usw/.lock` открывается с `O_RDWR | O_CREAT` без проверки link/reparse/type. В эксперименте эта ссылка заранее указывала на отсутствующий файл вне проекта; `read_handoff` создал там пустой файл ещё до чтения HANDOFF.

Ограничение доказательства: pathname backend принудительно выбран на macOS, `msvcrt.locking` заменён fake; операции с файлами настоящие. Native Windows locking и Windows reparse points не проверялись. Найден необработанный путь в коде, но не доказана эксплуатация на реальной Windows.

Исправление: открывать lock через общий контроль link/reparse/type, с no-follow там, где он доступен. Проверка: обычная и dangling symlink, неожиданный тип `.lock` отвергаются до внешних записей; дополнительно выполнить native Windows регрессию. Это заранее существующая ссылка, а не заявленное ограничение конкурентной подмены pathname backend.

**S07 · P2 · Изменение `flows.root` во время staging обнаруживается после записи**

Места: [загрузка плана:787](/Users/leonidkim/Documents/projects/usw/skills/usw-run-flow/scripts/run_flow.py:787), [финальный recheck:749](/Users/leonidkim/Documents/projects/usw/skills/usw-run-flow/scripts/run_flow.py:749), [readback:834](/Users/leonidkim/Documents/projects/usw/skills/usw-run-flow/scripts/run_flow.py:834).

После staging существующего `usw/flows/review.md` конфигурация изменена на `flows.root: alternate`. Финальный recheck не перечитывает решение о root; старый файл получает `New`, новый root не получает файл. Лишь readback сообщает `write_unverified`, `written: true`.

Исправление: непосредственно перед replace заново получить canonical authoring root и сравнить с подготовленным решением. Проверять семантическое изменение выбранной цели, а не любые косметические изменения YAML. Проверка: изменение root во время staging → `stale_flow_target`, старое содержимое сохранено. Изменение происходит до финальной проверки; residual CAS после неё в finding не входит.

**S08 · P2 · CLI принимает буквальный input за управляющую опцию**

Место: [предварительный просмотр argv:1108](/Users/leonidkim/Documents/projects/usw/skills/usw-run-flow/scripts/run_flow.py:1108).

`resolve <project> <root> review --origin shared -- --experimental-structured` возвращает `structured_runtime_removed`; такой же вызов с последним аргументом `--origin=local` — `invalid_flow_origin`. После `--` оба значения являются непустым пользовательским input. Предварительный проход игнорирует разделитель. Обратный случай: `--orig local --origin shared` проходит, поскольку argparse разрешает сокращение, а ручной счётчик его не распознаёт.

Исправление: проверять опции с учётом границы `--` и результата разбора, отключить неподдерживаемые сокращения. Проверка: оба буквальных input сохраняются точно; дубли selector через сокращения отвергаются. API и CLI должны принимать одинаковые значения input.

**S09 · P2 · Ошибка кодировки stdout скрывает уже состоявшуюся запись**

Места: [JSON serializer:1081](/Users/leonidkim/Documents/projects/usw/skills/usw-run-flow/scripts/run_flow.py:1081), [вывод после write:1212](/Users/leonidkim/Documents/projects/usw/skills/usw-run-flow/scripts/run_flow.py:1212).

При `PYTHONIOENCODING=ascii`, `PYTHONUTF8=0` команда write успешно сохраняет UTF-8 Markdown «Русский Markdown.», затем `ensure_ascii=False` приводит к `UnicodeEncodeError` в stdout. Наблюдалось: exit 1, stdout пуст, файл изменён. Вызывающий не получает JSON и признака `written: true`.

Исправление: выводить JSON с `ensure_ascii=True` либо явно обеспечить UTF-8 транспорт; escape-последовательности JSON сохраняют Unicode после декодирования. Проверка: write и inspect с не-ASCII содержимым и ограниченной кодировкой stdout возвращают корректный JSON с исходным текстом. Это подтверждено для названного окружения; обычная Windows-конфигурация автоматически не считается сломанной.

**S10 · P2 · Ошибка обновления оставляет компонент удалённым или установку частичной**

Места: [preflight:55](/Users/leonidkim/Documents/projects/usw/install.sh:55), [замена skill:84](/Users/leonidkim/Documents/projects/usw/install.sh:84), [замена команды:99](/Users/leonidkim/Documents/projects/usw/install.sh:99).

После обычной установки во временный `QWEN_HOME` запущен `--force` из копии пакета без `usw-manage-handoff`. Старый компонент сначала удалён, затем `cp` завершился ошибкой; exit 1, прежнего skill нет, предыдущий компонент уже обновлён. Предварительная проверка полноты источников отсутствует.

Связанный случай preflight: `[ -e ]` не видит dangling symlink на `commands/usw-init.md`. И обычная установка, и `--force` завершаются ошибкой копирования после установки шести skills; force не заменяет ссылку. На проверенной macOS внешнего файла не создано — выход за каталог здесь не подтверждён.

Исправление: до изменений проверить все источники и конфликты, учитывать `-L`. Каждую замену сначала подготовить рядом с destination; сохранить возможность вернуть прежний компонент, если замена не удалась. Глобальная транзакция всей установки не требуется. Проверка: отсутствующий source/ошибка копирования сохраняют рабочую старую копию; dangling target без force отклоняется до установки, с force заменяется.

**S11 · P2 · Путь установки может совпасть с источником и уничтожить его**

Места: [настройка QWEN_HOME:38](/Users/leonidkim/Documents/projects/usw/install.sh:38), [source/target:81](/Users/leonidkim/Documents/projects/usw/install.sh:81).

В полной временной копии пакета `QWEN_HOME` назначен равным корню этой копии. `qwen --force` удаляет собственный `skills/usw-initialize-project`, затем падает при копировании отсутствующего источника. Это ошибочная, но допускаемая настройка публичного override.

Исправление: до очистки отклонять каноническое совпадение или пересечение source/target компонентов, включая aliases через symlink. Проверка: прямое совпадение и alias дают отказ до первой мутации, все исходные файлы сохранены. Одной проверки строковых путей недостаточно.

**S12 · P2 · Успешный upgrade оставляет снятые с поставки skills**

Места: [legacy список:35](/Users/leonidkim/Documents/projects/usw/install.sh:35), [cleanup:110](/Users/leonidkim/Documents/projects/usw/install.sh:110).

В legacy cleanup отсутствуют ранее поставлявшиеся `usw-brainstorm-solutions` и `usw-manage-artifacts`. История installer подтверждает удаление первого из поставки в `ce1148c75f39cc8b5218b6cfc56c51c1b40bdc5e`, второго — в `1814ac19db77b9f56d91fec0881d495e0d9fd985`, без добавления в legacy. Исторический статус второго прямо указан в [research README:12](/Users/leonidkim/Documents/projects/usw/research/structured-runtime/README.md:12).

В tempfile созданы прежние каталоги обоих skills, затем текущий `qwen --force` завершился с кодом 0. Новые компоненты появились, оба старых каталога сохранились и остаются доступны механизму обнаружения skills.

Исправление: добавить два точных исторических имени в существующий legacy cleanup. Проверка: после успешного upgrade оба отсутствуют, посторонние навыки сохранены. Это отдельная неполнота миграции installer, а не ранее описанные дубли OpenSpec или отставшие установленные версии USW.

**S13 · P2 · Явно пустой `--runner` не перекрывает переменную окружения**

Место: [выбор команды:674](/Users/leonidkim/Documents/projects/usw/evals/run_evals.py:674); документированный приоритет — [evals README:35](/Users/leonidkim/Documents/projects/usw/evals/README.md:35).

`args.runner or getenv(...)` смешивает отсутствие параметра и явную пустую строку. При заданном `USW_EVAL_RUNNER` вызов `--runner ''` запускает команду из окружения. Локальный stub: exit 0, один вызов runner, сценарий не skipped. Для обёртки, передающей пустую строку с намерением отключить runner, это может неожиданно запустить платный внешний прогон. Реальный внешний runner в аудите не использовался.

Исправление: использовать значение CLI, если оно не `None`; отдельно обработать пустое/пробельное значение как отсутствие эффективной команды. Альтернатива — явно отклонять пустой CLI-параметр; молчаливый fallback нарушает обещанный приоритет. Проверка: absent/empty/whitespace/nonempty CLI при установленной и отсутствующей переменной; пустой override не вызывает runner.

**S14 · P2 · Transcript теряет исходный вывод упавшего runner**

Места: [обработка ошибки:376](/Users/leonidkim/Documents/projects/usw/evals/run_evals.py:376), [запись transcript:567](/Users/leonidkim/Documents/projects/usw/evals/run_evals.py:567). Документация обещает [raw runner output:36](/Users/leonidkim/Documents/projects/usw/evals/README.md:36).

Stub печатает `AUDIT_STDOUT_EVIDENCE`, две строки stderr и завершается с кодом 3. Harness возвращает корректный exit 2, но файл transcript содержит только `<runner error: runner exited 3: last line>`. Весь stdout и первая строка stderr потеряны. Timeout-ветка также отбрасывает частичный вывод из исключения. Это лишает диагностику свидетельств того, что происходило до сбоя.

Исправление: хранить stdout, stderr и returncode/error отдельно от поведенческого вердикта; при `--transcripts` сохранять полный доступный вывод, включая частичный timeout output. Краткий экранный отчёт можно оставить. Проверка: ненулевой exit и timeout сохраняют выданный stub-текст, оставаясь runner errors, а не behavior failures.

**Пробелы проверки и предложения по формулировкам**

| Участок | Уточнение контракта | Практическое улучшение |
| --- | --- | --- |
| Handoff mutation | «Ошибка после replace означает неподтверждённый результат. Перечитать сохранённые документы; не удалять их, пока неизвестно, опубликован ли маршрут» | S01; отдельные инъекции ошибок до replace, после replace, на sync и readback |
| Writer | «Перед заменой проверить текущий root и identity parent; при очистке удалять только объект, созданный этой попыткой» | S02/S07; обычная directory substitution наряду с symlink substitution |
| CLI write | «Код завершения сам по себе не доказывает отсутствие записи; успешная запись должна иметь машинно читаемый результат» | S09; ограниченная кодировка stdout в регрессии |
| Installer | «Force заменяет установленные USW-компоненты; источники и пути проверяются до удаления, ошибки конкретной замены сохраняют старую копию» | S10/S11; формулировку обещания вводить вместе с реализацией |
| Eval runner | «CLI-параметр перекрывает окружение, включая явно пустое значение; runner error сохраняет доступный вывод» | S13/S14; precedence и evidence проверять раздельно |

В [CI](/Users/leonidkim/Documents/projects/usw/.github/workflows/ci.yml) есть Linux и Windows, но нет macOS. Это пробел покрытия относительно требования [запускать suite на каждой объявленной платформе:89](/Users/leonidkim/Documents/projects/usw/openspec/specs/cross-platform-safe-access/spec.md:89), а не отдельный доказанный runtime-дефект. Добавить macOS job существующей deterministic suite; S05 показывает, почему одного Linux недостаточно. Native Windows проверки S06 должны дополнять fake-backend тест.

Уточнение прежней E03: противоречие модели полномочий находится также в [flow-behavior-evaluation:97](/Users/leonidkim/Documents/projects/usw/openspec/specs/flow-behavior-evaluation/spec.md:97). Там blanket-правило относит к недоверенным заявлениям и `user input`. Разделение поддельного разрешения в flow и прямого разрешения пользователя нужно согласовать в spec и сценариях одновременно. Новой находкой это не считается.

**Что проверено успешно и что не является новой находкой**

| Существующий набор | Тестов | Результат |
| --- | ---: | --- |
| `test_handoff_state.py` | 55 | OK |
| `test_init_usw.py` | 25 | OK |
| `test_platform_support.py` | 19 | OK |
| `test_flow_orchestrator.py` | 55 | OK |
| `test_end_to_end.py` | 4 | OK |
| `test_install.py` | 4 | OK |
| `test_package_layout.py` | 24 | OK |
| `test_eval_harness.py` | 55 | OK |

Итого 241 различный тест в восьми целевых наборах; повторный запуск platform suite двумя проверяющими не удваивает охват. Это продолжение ранее проведённого полного прогона 275 тестов, а не новый полный прогон. Дополнительные fault-injection эксперименты выявили случаи за пределами существующих assertions.

Подтверждены обычные отказы symlink/type/traversal, immutable operation identity/input, stale Outcome/Save после Finish, конкурентные операции с разными identity, сохранение существующих initializer files. Writer сохраняет BOM/CRLF и identity исходных байтов. Новых доказанных проблем в manifests не найдено.

Не включены в дефекты: явно исключённое окно CAS после final recheck; документированная более слабая concurrency guarantee pathname backend; нормализация переводов строк в `equals_flow`, которая уже раскрыта в [notes сценария](/Users/leonidkim/Documents/projects/usw/evals/scenarios/create-number-discuss/expect.json:21). Последнее ограничивает доказательность сравнения, но не является скрытой новой находкой.

Живые модели, внешние агенты/plugin managers, нативные Linux/Windows и удалённые CI-прогоны в этом этапе не запускались. Отсутствие новых находок по ним не означает подтверждённую корректность.

**Порядок последующих исправлений**

1. S01 и S02: сохранность recovery state и соответствие записываемого/удаляемого каталога выбранному объекту. Два отдельных изменения с независимыми регрессиями.
2. S03–S07: повтор после partial write, общий safe access initializer/lock, filesystem aliases, финальная проверка root. Не объединять все случаи в большой рефакторинг.
3. S10–S12: безопасная замена одного компонента, проверка source/target overlap, полный известный legacy cleanup.
4. S08/S09: корректный разбор input и надёжный JSON-транспорт.
5. S13/S14 и CI: точный выбор runner, сохранение evidence, регулярная проверка macOS.

Готовность каждого изменения — отдельный наблюдаемый исход из соответствующего пункта. Исправления и новые постоянные тесты в рамках этого аудита не применялись.
