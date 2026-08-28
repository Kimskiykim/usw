## Why

`usw-create-flow` всё ещё поручает модели разрешение настроенных корней, выбор
раскладки flow и проверки безопасности файловой системы. Это уже приводило к
записи flow по неверному пути, тогда как остальные flow-скиллы делегируют
такие решения детерминированному resolver.

## What Changes

- Расширить CLI существующего flow resolver детерминированной подготовкой и
  атомарной записью entrypoint без отдельного authoring-скрипта.
- Разрешать shared root из `usw.yaml` открытого проекта, с `usw/flows` как
  standalone-дефолтом.
- Сохранять существующую flat/package раскладку, выбирать package для нового
  flow, отклонять неоднозначные и небезопасные пути и повторно проверять цель
  непосредственно перед записью.
- Возвращать неизменяемый существующий Markdown при подготовке и перечитывать
  сохранённый UTF-8 entrypoint после записи, не просматривая соседние ресурсы.
- Заменить в `usw-create-flow` модельные инструкции по путям и безопасности на
  вызовы команд resolver.
- Добавить детерминированные unit-тесты и model eval-сценарии для default shared
  authoring и нестандартного `flows.root`.
- По итогам ревью: создавать отсутствующий lazy flow root при `write`
  (отсутствующая `.usw` останавливает с `workspace_not_initialized`),
  отклонять пустой Markdown (`empty_flow_content`), выравнить разбор
  `flows.root` в общем config parser, различать отказ после состоявшейся
  замены (`write_unverified`), убирать созданные при отказе пустые каталоги,
  сохранять обычные права файлов и вернуть JSON-контракт ошибок для
  искажённого token.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

- `local-custom-flows`: потребовать подготовку и повторную проверку authoring-
  записи resolver в выбранном local или настроенном shared origin.

## Impact

- `skills/usw-run-flow/scripts/run_flow.py` получает authoring-субкоманды без
  изменения контрактов `resolve`, `inspect` и `resource`.
- `skills/usw-create-flow/SKILL.md` делегирует им выбор entrypoint и запись.
- Расширяется resolver-, platform-, skill-contract- и opt-in eval-покрытие.
- Не добавляются runtime dependency, Markdown parser, resource editor,
  изменение design scan или синхронизация packaged-flow спеки.
