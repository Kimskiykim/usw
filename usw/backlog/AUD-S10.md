# AUD-S10 — Ошибка обновления оставляет компонент удалённым или установку частичной

- Статус: принято
- Приоритет: P2
- Категория: находка аудита
- Действие: Проверять комплект источников/конфликты до установки; готовить замену каждого компонента до удаления старого, учитывать dangling symlinks.
- Условие возврата: следующая правка installer
- Критерий готовности: missing source/copy failure сохраняют прежний компонент, force корректно заменяет ссылку. Глобальная транзакция установки не требуется.
- Источник: [Аудит S10](/Users/leonidkim/Documents/projects/usw/usw/reviews/skills-prompts-audit-2026-10-03/SECONDARY_AUDITS.md:102)

## История

- 2026-11-10: реализованы preflight и сохранная замена отдельного компонента;
  контракт — [спецификация установки](../../openspec/specs/component-installation/spec.md),
  fault-сценарии — [тесты installer](../../tests/test_install.py). Глобальная
  транзакция, восстановление после сбоя питания, родительские symlink и AUD-S11
  вне scope.
- 2026-11-10, первоначальная native CLI проверка (`0.146.0`): host binding
  подтверждён, оба model requests завершились HTTP 400 `model_not_found` до
  действий модели; выполнение Init/Resume эти попытки не подтвердили.
  См. [первый CLI отчёт](../../.usw/state/autonomous-improvement/2026-11-10/s10-native-cli-probe-report.md).
- 2026-11-10, итоговая приёмка исправления: критерии missing source/copy failure
  и force подтверждены, независимый критик принял результат; полный suite —
  [299/299](../../.usw/state/autonomous-improvement/2026-11-10/s10-closeout-full.log).
  Реальная переустановка Codex успешна, сверены 73 файла шести skills и 10 commands;
  оба межсессионных случая Save → Resume подтверждены. История реализации и
  проверок относится к task `1.1` change `preserve-installed-components-on-failure`.
- 2026-11-10, bundled public CLI `0.167.0-alpha.3.2`, Terra/xhigh: native
  Init/Resume выполнили реальные tool actions с exit 0 и filesystem assertions;
  [отчёт и первичные logs](../../.usw/state/autonomous-improvement/2026-11-10/s10-appcli-native-evidence/report.md).
  На дату этих проверок Desktop picker и Linux не входили в подтверждённый охват.
