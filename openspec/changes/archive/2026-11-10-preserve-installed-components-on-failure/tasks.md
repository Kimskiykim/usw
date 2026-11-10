# Tasks

## 1. Сохранность установленного компонента

Repair1 по `s10-c3`: настроить project `usw.yaml` по design §5 и усилить
постоянные full-tree assertions target/backup/new tree по §4. Defaults и
installer capability delta не менять. До окончательного manifest учесть sync
main spec и изменения включённых `usw/` материалов; повторить обязательные checks.

- [x] 1.1 [Защитить обновление от ошибки подготовки и переключения](tasks/1.1-preserve-component/task.md). DoD: контракт task и все сценарии delta выполнены в `install.sh`, отрицательные тесты добавлены в `tests/test_install.py`, README ссылается на новую spec без обещания общей транзакции. Proof: сначала red на исходном installer, затем green адресных и полного unittest, `sh -n install.sh`, strict validate и `git diff --check`; фактические результаты с revision/source записаны Development. Обновить stable-token проверки путей/имён компонентов в `tests/test_install.py` вместе с fixture assertions, проверить anchors существующих package-тестов; новых phrase assertions не добавлять. `SKILL.md` не меняется, поэтому behavior evals для этой правки неприменимы.

Порядок внутри 1.1: воспроизведение → preflight → staging/rollback →
leaf symlink/ошибки очистки/диагностика → обзор документации → проверки source.
Обязательная fault-матрица включает partial copy обоих типов, bytecode cleanup,
final cleanup и последовательные отказы активации/восстановления из design.
Стабильный контракт и подробная матрица — по ссылке; checkbox здесь является
единственным completion source coding task и не означает Testing/Delivery.

## Workflow follow-up

- Локальный operational flow для принятого apply создавать отдельно через USW;
  shared `dev-test` и product scope S10 не менять ради организации команды.
- Независимый критик проверяет актуальные source, отрицательные tests и
  evidence. Исправления открывают ту же задачу новой попыткой; после двух
  возвратов без прогресса оркестратор передаёт аналитику разбор причины.
- Testing выполняет независимую fixture-проверку; после принятия кандидата
  назначенный писатель обновляет Codex отдельным шагом. Новый тестировщик
  сверяет установку и выполняет полезный USW-сценарий по design Migration Plan.
  Результаты — Testing evidence этой задачи и неизменяемые review receipts по
  `execution-artifacts`. Автор evidence другой роли его не переписывает.
- После фактической приёмки выполнить verify, sync и archive по применимым
  OpenSpec workflows; сохранить команды и вердикты. Аналитик обновляет историю
  AUD-S10 и его индекс, обосновывает необходимость изменения постоянного
  контекста либо отсутствие нового постоянного факта. Финальный коммит делает
  назначенный коммитер по принятому diff. Другие changes не архивировать.
