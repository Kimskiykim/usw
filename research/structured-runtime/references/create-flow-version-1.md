# Линейный контракт версии 1

Использовать этот legacy reference только после явного запроса strict версии
`1`. Ordinary Markdown является default и не использует этот contract.

## Форма

Сохранить существующую форму без изменений:

```markdown
# Flow: plan-check

<краткая цель и важные условия; необязательно>

## Контракт

- Версия: `1`

## Порядок действий

1. Скилл: `usw-plan-small-steps`
2. Скрипт: `scripts/check_plan.py`
   - Аргументы: `--strict`
```

- Оставлять обязательные секции ровно в указанном порядке.
- Нумеровать шаги подряд с `1`.
- Разрешать только точный skill или безопасный project-local script.
- Указывать `Аргументы` только у script, каждое значение в отдельных
  backticks; не использовать shell-строки, substitution, redirection или pipes.
- Не добавлять `Пишет` и раздел `Полномочия записи`. Runner получает
  write-contract skill из executor; script всё равно требует отдельного
  разрешения на запуск.
- Не добавлять branches, loops, retries, параллельность или произвольные
  переходы.

При редактировании существующего verbose-flow сохранять его legacy
write-metadata. Не создавать смешанную форму: либо прежние `Пишет` и
`Полномочия записи` присутствуют полностью, либо отсутствуют полностью.

## Проверка и отчёт

Разрешить validator относительно основного `SKILL.md` как
`../usw-run-flow/scripts/run_flow.py` и запустить:

- shared root: `python3 <validator> validate --experimental-structured <flows.root> <name>`;
- local root: `python3 <validator> validate --experimental-structured --local <project-root> <name>`;
  `-l` имеет ту же семантику.

Сообщить имя, origin (`shared` или `local`), путь, версию, шаги и точную команду
запуска: `$usw-run-flow --experimental-structured <name> <task>` либо
`$usw-run-flow --experimental-structured --local <name> <task>`.
