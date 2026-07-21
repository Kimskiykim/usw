# Задача 1.1: Реализовать общий контракт конфигурации v1 и review root

## Artifact model

- `legacy`

## Результат

USW создаёт, читает и валидирует согласованные поля `usw.yaml` v1 и безопасно
разрешает все configured roots внутри проекта, включая provider-neutral
`reviews.root`.

## Область

- Добавить default template конфигурации v1.
- Определить provider, общий artifact root, refinement root, flow root и review
  root со значениями по умолчанию из design.
- Разбирать и валидировать закрытое значение provider `standalone|openspec`, но
  не вызывать provider adapter и не выполнять OpenSpec artifact operations.
- Возвращать config error `unsupported_provider` для любого значения вне enum до
  runtime dispatch или managed write.
- Валидировать schema version и managed roots до любой managed write.
- Отклонять absolute paths, parent traversal, symlinks и конфликтующие writable
  roots.
- Разрешать только нормативное standalone containment специализированных roots
  внутри `artifacts.root`; отклонять их взаимное пересечение и overlap с project
  root, `.git` или `.usw`.
- Использовать `openspec` как default planning root только при явно выбранном
  OpenSpec provider, сохраняя provider-neutral USW roots под `usw/`.
- Сохранять существующий configuration file и неизвестные непротиворечивые поля.

## Вне области

- Изменение пользовательского поведения `/usw-init`.
- Семантическое OpenSpec artifact mapping.
- Operational activation OpenSpec adapter и выполнение provider capabilities.
- Сторонние providers и generic YAML hooks.

## Ссылки

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/workspace-configuration/spec.md`

## Зависимости

- Нет.

## Критерии готовности

- Defaults v1 точно соответствуют design, включая `usw/reviews`.
- Неподдерживаемые версии и unsafe roots отклоняются до записи.
- Неизвестное provider value возвращает `unsupported_provider`, не доходя до
  runtime `unsupported_provider_operation`.
- Валидные project-relative roots разрешаются от ближайшего project root.
- Standalone defaults с общим namespace проходят validation, а пересекающиеся
  specialized roots и reserved-area overlaps отклоняются.
- OpenSpec defaults не выводятся из наличия `openspec/` и разрешаются config
  layer только для явно выбранного provider; operational behavior остаётся 5.1.
- Validation не перезаписывает существующий configuration content.

## Проверка

- Запустить: `python3 -m unittest tests.test_init_usw -v`
- Ожидание: проходят сценарии создания configuration, review root, path safety
  provider-specific defaults, разрешённого standalone containment и отказа при
  конфликте без записи.
