# Калибровка assessment (usw-assess-flow)

Читать при неочевидном вердикте или спорной классификации цикла. Для обычного
assessment этот файл не нужен: SKILL.md самодостаточен.

## Почему approval не делает повтор безопасным

Approval один раз до цикла не делает повтор необратимого действия безопасным:
разрешение дано на одно исполнение, а не на неограниченную серию. Approval
внутри каждой итерации остаётся permission boundary, но сам по себе не
доказывает безопасную повторяемость side effect — он лишь останавливает каждый
повтор для решения человека. Защитой считать idempotency guarantee либо
структуру, где irreversible action и его approval находятся вне цикла.

## Калибровочные случаи

- finite terminal path → `executable`;
- bounded retry с terminal fallback → без blocking finding;
- A → B → A без выхода → `not-executable` с blocking finding;
- повторять до успеха без предела → `executable-with-risks` с risk finding;
- missing mandatory dependency без fallback → `not-executable`;
- missing dependency с `decision_required` → не blocking;
- mandatory call с retired selector без fallback → `not-executable`;
- approval перед loop с irreversible action внутри → `not-executable`;
- необратимый side effect внутри цикла → `not-executable` с blocking
  `unsafe-repeat` finding.
