# Проверка AUD-F02

Дата: 2026-10-09.

## Результат

Исправлен контракт общего `opsx-intent2spec`: полный состав выбранной схемы
берётся из CLI, все компоненты и glob-файлы охвачены структурной проверкой,
intent drift и feasibility. Имена схем и привычных файлов не ограничивают
scope. Роль задач определяется инструкциями; схема без задач не получает
выдуманный tasks-файл. Пропуски обоснованы, неполное чтение блокирует успех.

Запись выполнена через prepare-write/write с актуальным токеном; возвращённый
Markdown совпал с записанным. Main `intent-to-spec-planning` синхронизирован
с delta. Независимое ревью не обнаружило конкретных defects.
AUD-F02 удалён из активного бэклога как исправленный дефект инструкции;
это не заявление о доказанном поведении модели.

## Детерминированные проверки

- Новый stable-token тест сначала дал ожидаемый FAIL: отсутствовали CLI
  contract и полный review scope, присутствовали старые жёсткие пути.
  После правки все 8 тестов `test_flow_scenarios.py` проходят.
- Полный `python3 -m unittest discover -s tests -q`: 282 теста, 281 проходит;
  один прежний `FileNotFoundError` в
  `test_codex_marketplace_points_to_plugin` из-за отсутствия
  `.agents/plugins/marketplace.json`. До этой правки тот же сбой был
  воспроизведён на HEAD при предыдущем change.
- Strict validation change `check-all-schema-artifacts` и main spec
  `intent-to-spec-planning`: проходят.
- `openspec validate --all`: 24 из 24 проходят с прежними предупреждениями
  о длинных requirements в других спецификациях.
- `git diff --check`: проходит.

## Реальные ответы CLI

Во временном проекте с настоящим OpenSpec CLI проверены:

- `spec-driven`: tasks уже done, но specs отсутствуют и имеют ready.
  Состав и фактический changeRoot получены из CLI.
- Собственная схема `decision-driven`: brief, constraints и decision
  находятся в planning/, checks/ и review/. Proposal, design и tasks нет;
  instructions разрешает glob constraints в два конкретных файла.
- После удаления одного обязательного glob-файла status constraints остаётся
  done. Пропуск обнаружим только сравнением инструкций с existingOutputPaths.

Пути CLI сравнивались с каноническим временным root: CLI разрешает системный
alias временного каталога. Постоянных изменений тестового проекта не осталось.
Эти проверки подтверждают поля CLI, а не исполнение flow моделью.

## Поведенческие проверки

`intent-missing-delta-spec` и `intent-schema-extra-component` загружаются
harness без ошибок, но оба пропущены: runner не настроен. Пропуск не считается
успешным наблюдением поведения.

Сценарии адресно проверяют шаг 6 и reviewer gate-7.1 по снимкам CLI и файлам
fixture. Они не являются полным запуском flow, проверкой вызова CLI, второго
reviewer-а или native discovery. Stable-token тест подтверждает текстовый
контракт, а не полноту будущего модельного ревью.

## Переименование flow

По указанию владельца flow переименован в `opsx-intent2spec`. Сохранена
исходная flat-раскладка `usw/flows/opsx-intent2spec.md`; старый entrypoint
удалён. Обновлены frontmatter, заголовок, команда запуска, namespace новых
decision logs и актуальные ссылки в cookbook, бэклоге, тестах, evals и change.
Исторические аудиты и архивные changes сохраняют прежнее имя.

Штатный resolver возвращает новое имя и фактический flat-путь; 8 адресных
тестов, strict validation change и diff check проходят. Все 43 behavior
сценария загружаются, но пропущены без настроенного runner. Flow не запускался.
