# Refinement decisions: Execution evidence open questions

## `D-001` — Инвалидировать evidence на уровне всей задачи

- Case: `C-001`
- Status: accepted
- Decided: 2026-07-21T12:42:01+03:00
- Decision: любое изменение contract revision или source identity задачи делает
  всё связанное Development и Testing evidence этой задачи stale.
- Basis: пользователь выбрал консервативное правило для v1; оно однозначно и не
  допускает использования проверки против изменённого контракта или source.
- Consequences: старые evidence entries сохраняются как факты прежней попытки,
  но все обязательные Development и Testing checks требуется повторить; иногда
  это создаёт избыточные reruns.
- Supersedes: None.
- Follow-up cases: None.

## `D-002` — Закрепить OpenSpec 1.6.0

- Case: `C-002`
- Status: accepted
- Decided: 2026-07-21T12:42:45+03:00
- Decision: использовать точную версию OpenSpec `1.6.0` как первый
  release-blocking compatibility target.
- Basis: эта версия уже установлена локально и успешно валидирует текущий
  OpenSpec change; пользователь выбрал её вместо дополнительного version matrix.
- Consequences: CI и test config должны фиксировать `1.6.0`; проверка latest
  остаётся отдельной видимой и неблокирующей, а изменение pin требует явного
  обновления с успешным compatibility evidence.
- Supersedes: None.
- Follow-up cases: None.

## `D-003` — Отложить универсальные provider extensions

- Case: `C-003`
- Status: accepted
- Decided: 2026-07-21T12:43:49+03:00
- Decision: ограничить v1 двумя встроенными adapters — standalone и OpenSpec —
  и не добавлять declarative path mapping либо executable provider/plugin API.
- Basis: пользователь выбрал минимальную границу v1; второго реального provider,
  из требований которого можно вывести устойчивый extension contract, пока нет.
- Consequences: неподдерживаемый provider возвращает structured error без
  fallback writes; mapping или plugin API рассматриваются отдельным change после
  появления второго реального consumer.
- Supersedes: None.
- Follow-up cases: None.
