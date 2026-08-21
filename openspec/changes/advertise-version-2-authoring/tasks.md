## 1. Защитить поведение сценарием

- [x] 1.1 Добавить scenario `create-advertises-version-2`, который требует
  неблокирующее уведомление и отсутствие записи до согласования черновика.
- [x] 1.2 Дополнить `create-flat-edit` запретом лишнего уведомления и проверить
  загрузку всех сценариев. `ScenarioLoadingTests`: 14/14 OK.
- [x] 1.3 На исходной инструкции измерить новый scenario три раза и записать
  наблюдаемый RED baseline. Codex runner: `0/3 [fail]`; во всех transcripts
  отсутствуют `version-2`, `--structured` и `-s`, файл не создан.

## 2. Изменить инструкцию

- [x] 2.1 Добавить в `usw-create-flow` согласованный русский текст для нового
  flow без `--structured` или `-s`, сохранив ordinary Markdown по умолчанию.
- [x] 2.2 Повторить новый scenario и `create-flat-edit` по три раза; записать
  GREEN rates и проверить transcripts. Оба scenario: `3/3 [pass]`. Во всех
  новых-flow transcripts уведомление стоит до черновика; flat-edit не получает
  уведомление и сохраняет обычный flat entrypoint.

## 3. Принять и установить

- [x] 3.1 Запустить полную suite на Python 3.10 и 3.13, strict OpenSpec и
  `git diff --check`. Python 3.10: 250/250 OK; Python 3.13: 250/250 OK;
  OpenSpec: 19 passed, 0 failed; diff check: exit 0.
- [x] 3.2 Перенести только feature-вставку поверх незакоммиченного перевода в
  основном checkout, переустановить USW и сверить установленные копии. Текущий
  checkout: 250/250 OK; 18 skill trees и 18 command files совпадают с
  установленными копиями; уведомление присутствует у Qwen, Codex и Claude.
- [x] 3.3 Записать фактические результаты проверок и оставить change готовым к
  отдельной проверке и архивации. RED: 0/3; GREEN: новый scenario 3/3,
  flat-edit 3/3.
