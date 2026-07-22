# Flow: dev-test

Реализует выбранное OpenSpec-изменение, затем независимо проверяет соответствие
результата change и отсутствие лишних изменений. Отдельно проверяет diff на
избыточную сложность. Замечания reviewers не исправляются автоматически.

## Контракт

- Версия: `1`

## Порядок действий

1. `capture-baseline` — основной чат перед реализацией сохраняет read-only
   снимок текущего рабочего дерева: status, изменённые файлы и существующий
   diff. Снимок нужен только для отделения уже имевшихся пользовательских
   изменений от изменений, внесённых этим flow.
2. Скилл: `openspec-apply-change`
   - Пишет: `implementation` `implementation-tests` `task-index`
3. `critical-result-review` — передать независимому SUBAGENT
   `critical-reviewer` OpenSpec change, результат реализации, task index и
   baseline. Reviewer выполняет одно read-only ревью через скилл
   `usw-structured-review`:
   - Scope: только изменения, внесённые flow после baseline, в сопоставлении с
     proposal, design, delta specs и tasks выбранного change.
   - Review focus: полнота реализации требований и тестов; изменения вне
     согласованного scope; случайно затронутые файлы; смешение с существующими
     пользовательскими правками; необоснованные рефакторинги; согласованность
     кода, документации, specs и task index.
   - Output contract: findings по убыванию серьёзности с файлами и строками;
     отдельные списки ожидаемо и подозрительно затронутых файлов; пропущенные
     проверки; итоговый verdict `clean` или `needs-attention`. Ничего не
     исправлять.
4. Скилл: `ponytail-review`
   - Пишет: нет
5. `present-reviews` — основной чат объединяет critical review и Ponytail
   review, добавляет собственную оценку и вызывает HUMAN `owner`; GATE: выбрать
   `iterate-findings`, `show-proposal` или `make-decision`.
   - IF `iterate-findings`: перейти к `handle-follow-up` и разбирать findings
     по одному, после каждого ожидая ответа человека.
   - ELIF `show-proposal`: перейти к `handle-follow-up` и сразу показать
     рекомендуемый основной чатам scope исправлений.
   - ELIF `make-decision`: перейти к `handle-follow-up` и запросить решение
     человека по дальнейшим действиям.
   - ELSE: запросить один из объявленных вариантов.
6. `handle-follow-up` — основной чат выполняет выбранный режим через HUMAN
   `owner`. Исправления, commit, push и другие mutations требуют отдельного
   явного решения человека и не входят в review-часть flow.

## Полномочия записи

- `implementation`
- `implementation-tests`
- `task-index`

Reviewer и Ponytail не имеют полномочий записи.
