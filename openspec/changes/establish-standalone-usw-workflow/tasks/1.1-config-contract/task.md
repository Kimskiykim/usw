# Задача 1.1: Реализовать общий контракт конфигурации v1 и review root

## Результат

USW создаёт, читает и валидирует согласованные поля `usw.yaml` v1 и безопасно
разрешает все configured roots внутри проекта, включая provider-neutral
`reviews.root`.

## Область

- Добавить default template конфигурации v1.
- Определить provider, общий artifact root, refinement root, flow root и review
  root со значениями по умолчанию из design.
- Валидировать schema version и managed roots до любой managed write.
- Отклонять absolute paths, parent traversal, symlinks и конфликтующие writable
  roots.
- Сохранять существующий configuration file и неизвестные непротиворечивые поля.

## Вне области

- Изменение пользовательского поведения `/usw-init`.
- Семантическое OpenSpec artifact mapping.
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
- Валидные project-relative roots разрешаются от ближайшего project root.
- Validation не перезаписывает существующий configuration content.

## Проверка

- Запустить: `python3 -m unittest tests.test_init_usw -v`
- Ожидание: проходят сценарии создания configuration, review root, path safety
  и отказа без записи.
