## 1. Ручная активация

- [x] 1.1 Добавить проверку native handoff policy в `test_package_layout.py`;
  увидеть отказ до правки metadata. Добавить три адресных behavior scenarios
  с проверкой отсутствия handoff записей и явными ограничениями наблюдения.
- [x] 1.2 Обновить handoff description, policy и начальную границу активации;
  согласовать командные prompts, README и main `live-operation-state`.
  Проверка: policy-тест проходит, служебные вызовы runner остаются прежними.
- [x] 1.3 Добавить нейтральную вводную harness для activation scenarios через
  optional `explicit_invocation: false`, сохранив default `true`. Проверка:
  два новых теста сначала не проходят, затем все тесты harness проходят;
  неверные типы отклоняются, прежние сценарии сохраняют вводную.

## 2. Проверка и бэклог

- [x] 2.1 Прогнать адресные runtime/manifest тесты, полный unittest suite,
  behavior evals и строгую валидацию нового change; проверить diff. Записать
  результаты и прежние сбои отдельно в `verification.md`.
- [x] 2.2 Отметить в AUD-I07 выполненную часть handoff; сохранить открытыми
  find/assess и матрицу активации. Проверка: карточка не объявлена закрытой.
