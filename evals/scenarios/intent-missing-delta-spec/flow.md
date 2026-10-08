Контекст: адресная проверка шага 6, не запуск flow сначала. Передан снимок
CLI для spec-driven; пути относительно текущей папки fixture. Контракт:

- changeRoot: planning/change;
- proposal: done, resolvedOutputPath и existingOutputPaths — planning/change/proposal.md;
- specs: done, resolvedOutputPath — planning/change/specs/**/*.md;
  existingOutputPaths — только planning/change/specs/csv-export/spec.md;
- design: done, путь planning/change/design.md;
- tasks: done, путь planning/change/tasks.md; applyRequires — tasks.

Инструкции specs требуют отдельный delta spec для каждой capability,
объявленной в proposal. Пропусков, skip_specs и условных компонентов нет.
Decision log: локальный экспорт CSV и маскирование секретов в отчёте. Уже
созданные файлы доступны в fixture; в этом сценарии ничего не дописывать.
