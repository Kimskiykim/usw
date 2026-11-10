# Tasks

## 1. Честный способ продолжения ожидания

- [x] 1.1 [Уточнить рецепт и проверить два режима продолжения](tasks/1.1-honest-wait-continuation/task.md)

DoD и весь proof — в linked v1 leaf `i13-wait-c1`: обновить рецепт, узкие
tests и main spec; проверить actual preview/действия ordinary roles в двух
режимах, counters/state/ответ, затем offline suite и strict validation на
конечном source. Это одна coding task с включённой проверкой и документацией.

## Workflow follow-up

- Independent critic проверяет все шесть frozen planning artifacts и evidence
  до отдельного apply. Current planning не разрешает реализацию.
- Development и Testing ведут раздельные evidence по leaf; blocking finding
  открывает ту же task новой attempt. При смене source все checks повторяются.
- До final source включить согласованные main-spec sync и точную отметку
  wait subitem в AUD-I13/index; два остальных subitems и `backlog` сохраняются.
- Установку/новую сессию, verify/archive и интеграцию назначать отдельно после
  независимой приёмки. Глобальная установка и другая копия не меняются.
- Общая цель и остальные карточки остаются открытыми; writer передаёт только
  этот change и local delivery pointer, без merge/index/commit/push.
