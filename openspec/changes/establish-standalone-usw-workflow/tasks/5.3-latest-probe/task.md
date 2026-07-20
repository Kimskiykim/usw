# Задача 5.3: Добавить видимый неблокирующий latest probe

## Результат

CI выполняет применимые compatibility scenarios с latest OpenSpec и показывает
tested version и failures, не блокируя USW release.

## Область

- Переиспользовать реальный compatibility runner в latest-version mode.
- Добавить отдельную CI job со статусом non-blocking.
- Публиковать resolved version и failure output для triage.
- Документировать намеренное продвижение успешной latest version в pinned target.

## Вне области

- Автоматическое изменение pinned version.
- Скрытие failures или преобразование их в passing result.
- Release-blocking matrix из нескольких версий.

## Ссылки

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/openspec-compatibility/spec.md`

## Зависимости

- Задача 5.2.

## Критерии готовности

- Latest job устанавливает и показывает resolved OpenSpec version.
- Она выполняет те же применимые behavioral scenarios, что pinned job.
- Failure остаётся видимым, но не нарушает release gate.
- Promotion в pinned требует явного version-controlled change.

## Проверка

- Запустить: `./tests/run_openspec_compatibility.sh latest`
- Ожидание: runner показывает resolved latest version и возвращает фактический
  scenario result; CI сохраняет failure, не блокируя pinned gate.
