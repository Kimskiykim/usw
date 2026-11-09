# Проверка AUD-I07: find/assess

Дата: 2026-10-09.

## Результат

Прямая обычная просьба найти или оценить именно flow принимается без имени
skill. Оба descriptions, начальные guards и native metadata согласованы.
Выбор хостом разрешён, но не заменяет прямое намерение человека. При неясном
объекте чтение откладывается до уточнения; простое упоминание и общая проверка
кода не активируют skills. Read-only scope и существующие selectors сохранены.

README содержит матрицу всех шести skills. Main flow-discovery и flow-assessment
синхронизированы с delta; остальные требования не менялись. Политика ручного
handoff и его служебные вызовы не менялись.

## Наблюдения модели

- Старый текст отверг обе обычные просьбы как недостаточные: baseline.md
  в evidence фиксирует ответы отдельного агента.
- Новый текст: finder фактически использовал resolve и вернул match;
  assessor использовал inspect без унаследованного origin и вернул executable.
- Общая проверка кода и простое упоминание не активировали skills; неясный
  объект вызвал вопрос до чтения конфигурации, каталога и entrypoint.
- Raw report, stdout загрузчиков и команды сохранены в evidence/observed.md;
  использованная fixture — evidence/fixture/.
- Parent сравнил все три файла fixture до/после побайтно: изменений нет.
  RAN.txt и operation directory не созданы, flow и Begin/Outcome не запускались.

Это ограниченное наблюдение по переданным candidate instructions, а не
native discovery или гарантия будущего поведения модели.

## Проверки

- Две изменённые policy-проверки и новый guard/matrix тест сначала дали FAIL;
  после правки 15 package flow тестов и 58 harness тестов проходят.
- Полный unittest suite: 286 тестов, 285 проходят. Единственный прежний сбой —
  отсутствующий `.agents/plugins/marketplace.json` в
  test_codex_marketplace_points_to_plugin; он ранее воспроизведён на HEAD.
- Strict validation accept-natural-flow-requests: проходит.
- OpenSpec validate all: 26 из 26 проходят с прежними предупреждениями
  длинных requirements других спецификаций.
- Delta/main blocks побайтно совпадают; diff check проходит.
- Независимое ревью actionable defects не обнаружило.

## Первоначальные ограничения

При первоначальной проверке все 51 harness behavior scenarios загружались,
но были пропущены без runner;
шесть новых activation scenarios используют explicit_invocation=false.
File sentinels наблюдают только конкретную ветку записи и не доказывают
отсутствие чтения; для этого нужен tool transcript.

На этом этапе native discovery и handoff behavior scenarios не проверялись,
глобальные установленные skills не обновлялись; AUD-I07 оставалась открытой.

## Дополнительная проверка установленного пакета, 2026-10-09

Обновлены глобальные установки Codex, Claude и Qwen; файлы сверены с исходниками.
В новых сеансах Codex CLI без передачи skill instructions выполнены 10 случаев:
find/assess, отрицательная и неясная активация, ручной handoff, а также flow с
handoff включённым и отключённым. Все процессы завершились успешно; 30 адресных
условий подтверждены tool transcripts и сравнением файлов.

С настроенным runner актуальные девять целевых harness scenarios прошли по 1/1.
Первоначальный false-negative проверки формата explicit-disabled сохранён;
input уточнён без изменения product instructions, повторный проход успешен.
Остальные behavior scenarios не выполнялись. Нативная проверка ограничена Codex
CLI; desktop GUI, Claude и Qwen как хосты активации отдельно не проверялись.

Доказательства и ограничения: [отчёт](evidence/native-2026-10-09/README.md).
AUD-I07 удалена из бэклога как закрытая.
