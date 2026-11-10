# Design

## Context

Причина и пользовательский эффект — [proposal](proposal.md#why).
`_parse_yaml_mapping` сохраняет в stack только mapping, поэтому строка после
scalar получает прежнего parent. В `run_flow.py` общий parser читает конфигурацию
только для shared authoring: `prepare_flow_write → _authoring_root → load_config`.
Handoff использует `handoff_state.py → _enabled_root → load_config`.
`resolve` получает готовый `shared_root`. В ролевом Run конфигурацию до этого
читает исполнитель по SKILL.md §Разрешение; `prepare-write` не доказывает этот
ролевой этап. В этой задаче проверяется реальный authoring caller и сохраняется
регрессия Run helper с переданным root, без добавления нового production caller.
Архитектурные границы: `openspec/context/03-architecture.md` и ADR-001.

## Goals / Non-Goals

Контракт поведения — [delta](specs/workspace-configuration/spec.md).
Выбор design ограничен structural validation общего parser; execution path,
сериализация конфигурации и write helpers сохраняются.

## Decisions

1. **Явный отказ от неподдержанного синтаксиса.** Block scalar отклоняется,
   включая header modifiers; проверка выполняется с учётом комментариев и
   уже поддерживаемых простых quoted scalar. Более глубокая строка допустима
   только в открытом mapping, не под scalar; возврат к родительскому mapping
   сохраняет настоящие sibling keys. Фиксированный шаг отступа не вводится.
   Непрозрачное пропускание block body потребовало бы новой грамматики его
   границ; full YAML/dependency не обоснованы этой находкой.
2. **Инертность действует внутри допустимого subset.** Fallback:25–26 уже
   требует игнорировать неизвестные поля, project-initialization требует
   эквивалентности двух init paths. Явный отказ от неподдержанного block syntax
   совместим с этими нормами; молчаливое исполнение его тела несовместимо.
   В fallback кратко закрепляется та же граница. Его специальное model
   исполнение не требуется; ошибка Python по прежнему останавливает init.
3. **Точки изменения заранее известны.** Production: только `init_usw.py` и
   `references/llm-fallback.md` внутри `skills/usw-initialize-project/`.
   Regression files: `tests/test_init_usw.py`, `tests/test_flow_orchestrator.py`,
   `tests/test_handoff_state.py`; для нормативных токенов — существующий
   `tests/test_package_layout.py` либо `tests/test_atomic_skill_contracts.py`.
   Caller code, SKILL.md, commands, templates, installer и harness не меняются.
4. **Один дом для каждого факта.** Main-spec sync добавляет только эту delta
   в `openspec/specs/workspace-configuration/spec.md`. После фактического proof
   и согласования future writer обновляет только `usw/backlog/AUD-T01.md`
   (результат и ссылки) и `usw/BACKLOG.md` (убрать открытую строку, пересчитать
   P2). Context уже ссылается на capability; README/context не пересказывают её.

## Risks / Trade-offs

- Ранее принятый block scalar теперь даёт ошибку → сообщение `invalid_config`
  до записи; исходная конфигурация сохраняется, исправление делает пользователь.
- Избыточная проверка отступов может отвергнуть валидные mapping/siblings →
  положительные контроли и фактический init входят в leaf proof.
- Ошибка в общем parser влияет на shared authoring/Handoff → проверять настоящие callers,
  не только словарь результата parser.

## Migration Plan

Planning завершается передачей независимому критику; apply требует отдельного
поручения. Полный DoD, команды, actual tree proof и fresh installed use
находятся только в [leaf](tasks/1.1-reject-invalid-scalar-structure/task.md).

Предварительные проверки и предметный review предшествуют согласованным
main-spec/card/index edits. **Final source фиксируется после всех этих
заранее известных included edits**; затем обязательные checks/evidence
подтверждаются для конечного source. Установка — отдельное назначение;
после неё используется новая рабочая сессия, а не специальный model probe.
Новые включённые исправления открывают новый source/check cycle; v1 evidence
и receipts прежней пары contract/source сохраняются как история целиком.

Обратная установка последнего принятого пакета — отдельное решение при
регрессии; пользовательские configuration/state автоматически не переписывать.
Roots, role ownership и точные будущие evidence paths заданы в leaf.

Оценка полного connected diff до реализации: 570–850 строк, включая примерно
300–350 строк planning, 140–220 code/tests, 70–100 нормативных/card/index edits
и 90–160 evidence/reviews. Это оценка, не лимит разрешения: около 1000+ строк
требуют отдельного согласия; F05≤1100 не переносится. Считать additions и
deletions всех связанных Git-visible файлов, включая untracked artifacts.
