## Context

`chat-review` является text-first Markdown flow: `$usw-run-flow` передаёт его
модели целиком, а `CALL`, `GATE` и `PARALLEL` остаются инструкциями для чтения,
не runtime DSL. Текущий flow фиксирует двух reviewer-ов, требует многословный
input и принимает одно решение для всех findings. Поставляемые examples также
могут ссылаться на bundled или external skills без явной классификации.

## Goals / Non-Goals

**Goals:**

- дать короткий profile-based способ настроить одинаковые или разные reviews;
- выбирать два или три review agents по объяснимой оценке риска;
- получать настоящий majority verdict через явные votes по каждому finding;
- ограничить эскалацию максимум тремя reviewer-ами;
- сохранить финальное human decision отдельно для каждого finding;
- сделать зависимости examples проверяемыми без исполнения flow.

**Non-Goals:**

- parser, normalized plan, scheduler, machine cursor или reviewer registry;
- доказательство корректности finding голосованием;
- автоматическая установка external skills;
- автоматическое исправление findings;
- изменение `$usw-run-flow`, handoff protocol или permission model.

## Decisions

### Profiles остаются inline Markdown

Flow определит named profiles как обычные блоки `Scope`, `Review focus` и
`Output contract`. `usw-structured-review` остаётся executor-ом, а
`usw-reviewer-llm-critic` — review focus.

Альтернатива — общий registry profiles. Она отклонена: второго независимого
consumer-а пока нет, а registry добавит resolver и lifecycle.

### `--reviewers` является параметром input

`--reviewers auto|2|3` читается из пользовательского input самим flow и не
становится selector-ом `$usw-run-flow`. `auto` использует фиксированный rubric:
один high-impact trigger или два uncertainty factors выбирают три агента,
иначе два. Основной агент показывает результат оценки до запуска reviewers.

Альтернатива — свободная самооценка без rubric. Она короче, но делает одинаковый
input нестабильным и не объясняет затраты.

### Discovery и voting разделены

Reviewers сначала независимо находят candidates. После дедупликации каждый
активный reviewer явно оценивает каждый candidate. Это не позволяет трактовать
пропущенный finding как `reject`.

При начальном budget 2 спорный candidate получает третьего reviewer-а. При
budget 3 все три участвуют сразу. После третьего агента цикл закрыт: majority
требует два одинаковых non-abstain votes, иначе решение остаётся человеку через
`decision_required`.

Альтернатива — считать количество одинаковых первоначальных findings. Она
отклонена, потому что отсутствие finding означает «не заметил», а не
«проверил и отверг».

### Majority является рекомендацией

Presentation показывает votes и evidence, но owner принимает
`fix-finding`/`reject-finding` для каждого ID. Это сохраняет простую majority
aggregation и допускает осознанное человеческое несогласие.

### Dependency closure проверяется только для examples

Каждый example объявляет `bundled` и `external` skills. Package test сравнивает
эти объявления с буквальными `CALL SKILL` references. Bundled skill должен
существовать и устанавливаться standalone installer-ом; external skill только
объявляется.

Проверка не интерпретирует control flow. Existing initialized examples
остаются user-owned и не перезаписываются; новый текст получают fresh
initialization или ручное повторное копирование.

### Handoff — результат, не автоматический запуск

Flow возвращает два множества findings и bounded scope следующего
implementation flow. При включённом generic handoff те же факты могут попасть
в operation outcome, но review не создаёт новый product artifact и не запускает
fix самостоятельно.

## Risks / Trade-offs

- [Второй voting pass увеличивает model calls] → запускать третий reviewer
  только для unresolved candidates и сохранять hard cap 3.
- [Model может по-разному применить rubric] → перечислить закрытые triggers и
  обязать показать выбранные факторы.
- [Static dependency scan хрупок к prose] → извлекать только literal
  `CALL SKILL` и строки dependency block, не строить parser.
- [External dependency отсутствует] → flow возвращает `decision_required` и
  не подменяет skill.
- [Существующие initialized examples останутся старыми] → сохранить
  create-only policy и дать manual copy guidance.

## Migration Plan

1. Обновить canonical packaged examples и shared `chat-review`.
2. Добавить dependency closure tests и обновить text-flow scenario tests.
3. Не перезаписывать существующие initialized examples.
4. При откате вернуть Markdown и tests; runtime/state migration не требуется.

## Open Questions

Нет блокирующих вопросов. Формат остаётся prose-first и может уточняться без
изменения runtime.
