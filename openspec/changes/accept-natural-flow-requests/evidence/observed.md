Порядок проверен: **C → D → E → A → B**. Candidate loading не считался вызовом.

| Запрос | Классификация | Вопрос | Действия на fixture |
|---|---|---|---|
| C «Проверь код в src/» | find/assess не активируются | Уточнение о flow не требуется | Никаких |
| D «У нас есть flow test-evidence, но сейчас просто обсуждаем сроки» | find/assess не активируются | Уточнение о flow не требуется | Никаких |
| E «Оцени flow» | assess активируется по намерению, загрузка отложена из-за невыбранного объекта | «Какой flow требуется оценить?» | Никаких |
| A «Найди flow для проверки результатов тестов» | find активируется; **match** | Не требуется | Конфигурация → прямые кандидаты → `resolve --origin shared` |
| B «Оцени flow test-evidence» | assess активируется; **executable** | Не требуется | Независимое чтение конфигурации → `inspect` без селектора |

Для C/D/E конфигурация, каталог и entrypoint не читались. В B origin из A не переносился: использовано самостоятельное разрешение «сначала локальный».

Результат A: `test-evidence`, origin `shared`; description прямо соответствует намерению. Путь: `/private/var/folders/pt/pg7fz4fd1_5fr07tng9zjbrw0000gn/T/usw-flow-activation-zv7x3cfb/usw/flows/test-evidence.md`.

Готовая команда, **не запускалась**:

```text
$usw-run-flow --shared test-evidence проверки результатов тестов
```

# Flow assessment

- Flow: test-evidence
- Origin: shared
- Path: /private/var/folders/pt/pg7fz4fd1_5fr07tng9zjbrw0000gn/T/usw-flow-activation-zv7x3cfb/usw/flows/test-evidence.md
- Directory: /private/var/folders/pt/pg7fz4fd1_5fr07tng9zjbrw0000gn/T/usw-flow-activation-zv7x3cfb/usw/flows
- Identity: usw-markdown:shared:6054d0734b9527dc481b382a4054de76f3a94e18aff3332eb2a6aba51e6fd93e
- Verdict: executable
- Basis: семантический анализ моделью по тексту; не машинная гарантия.

## Terminal paths

- Пустой вход → `decision_required`, строка 7.
- Непустой вход → получить результаты, перечислить ошибки и создать итоговый `RAN.txt` → `completed`, строки 7–9. Действия только анализировались.
- Циклов и неразрешённых переходов в тексте нет.

## Dependencies

None.

## Findings

None.

Предупреждения загрузчика: `[]`. Замечаний о метаданных нет. Вход сценария для B не передан; трасса сценария не строилась.

## Raw results

Конфигурация, прочитанная отдельно для A и B:

```yaml
schema_version: 1
handoff: false
```

Прямой каталог кандидатов A:

```text
local: root absent
shared: test-evidence flat
```

`resolve` A, raw stdout:

```json
{"flow_directory": "/private/var/folders/pt/pg7fz4fd1_5fr07tng9zjbrw0000gn/T/usw-flow-activation-zv7x3cfb/usw/flows", "identity": "usw-markdown:shared:6054d0734b9527dc481b382a4054de76f3a94e18aff3332eb2a6aba51e6fd93e", "input": "проверки результатов тестов", "markdown": "---\nname: test-evidence\ndescription: Проверить результаты тестов и перечислить обнаруженные ошибки.\n---\n# Flow: test-evidence\n\n1. Получить результаты тестов из входа. Если вход пуст, вернуть decision_required.\n2. Кратко перечислить ошибки и создать RAN.txt с итогом, только при выполнении flow.\n3. Завершиться с результатом completed.\n", "name": "test-evidence", "origin": "shared", "path": "/private/var/folders/pt/pg7fz4fd1_5fr07tng9zjbrw0000gn/T/usw-flow-activation-zv7x3cfb/usw/flows/test-evidence.md", "warnings": []}
```

`inspect` B, raw stdout:

```json
{"flow_directory": "/private/var/folders/pt/pg7fz4fd1_5fr07tng9zjbrw0000gn/T/usw-flow-activation-zv7x3cfb/usw/flows", "identity": "usw-markdown:shared:6054d0734b9527dc481b382a4054de76f3a94e18aff3332eb2a6aba51e6fd93e", "markdown": "---\nname: test-evidence\ndescription: Проверить результаты тестов и перечислить обнаруженные ошибки.\n---\n# Flow: test-evidence\n\n1. Получить результаты тестов из входа. Если вход пуст, вернуть decision_required.\n2. Кратко перечислить ошибки и создать RAN.txt с итогом, только при выполнении flow.\n3. Завершиться с результатом completed.\n", "name": "test-evidence", "origin": "shared", "path": "/private/var/folders/pt/pg7fz4fd1_5fr07tng9zjbrw0000gn/T/usw-flow-activation-zv7x3cfb/usw/flows/test-evidence.md", "warnings": []}
```

## Фактически использованные команды

Общая загрузка candidate instructions:

```sh
cat /Users/leonidkim/Documents/projects/usw/skills/usw-find-flow/SKILL.md /Users/leonidkim/Documents/projects/usw/skills/usw-find-flow/agents/openai.yaml
cat /Users/leonidkim/Documents/projects/usw/skills/usw-assess-flow/SKILL.md /Users/leonidkim/Documents/projects/usw/skills/usw-assess-flow/agents/openai.yaml /Users/leonidkim/Documents/projects/usw/skills/usw-assess-flow/references/assessment-model.md
```

После классификации C/D/E, для A:

```sh
cat /private/var/folders/pt/pg7fz4fd1_5fr07tng9zjbrw0000gn/T/usw-flow-activation-zv7x3cfb/usw.yaml
python3 -B /Users/leonidkim/Documents/projects/usw/skills/usw-run-flow/scripts/run_flow.py resolve --help
python3 -B /Users/leonidkim/Documents/projects/usw/skills/usw-run-flow/scripts/run_flow.py inspect --help
ruby -e 'root=ARGV[0]; {"local"=>".usw/flows", "shared"=>"usw/flows"}.each do |origin,relative|; dir=File.join(root,relative); begin; ds=File.lstat(dir); rescue Errno::ENOENT; puts "#{origin}: root absent"; next; end; abort "unsafe root #{dir}" unless ds.directory?; Dir.children(dir).sort.each do |entry|; path=File.join(dir,entry); s=File.lstat(path); if entry.end_with?(".md") && entry.delete_suffix(".md").match?(/\A[a-z0-9]+(?:-[a-z0-9]+)*\z/) && s.file?; puts "#{origin}: #{entry.delete_suffix(".md")} flat"; elsif entry.match?(/\A[a-z0-9]+(?:-[a-z0-9]+)*\z/) && s.directory?; ep=File.join(path,"FLOW.md"); begin; es=File.lstat(ep); rescue Errno::ENOENT; next; end; puts "#{origin}: #{entry} package" if es.file?; end; end; end' /private/var/folders/pt/pg7fz4fd1_5fr07tng9zjbrw0000gn/T/usw-flow-activation-zv7x3cfb
python3 -B /Users/leonidkim/Documents/projects/usw/skills/usw-run-flow/scripts/run_flow.py resolve --origin shared /private/var/folders/pt/pg7fz4fd1_5fr07tng9zjbrw0000gn/T/usw-flow-activation-zv7x3cfb /private/var/folders/pt/pg7fz4fd1_5fr07tng9zjbrw0000gn/T/usw-flow-activation-zv7x3cfb/usw/flows test-evidence 'проверки результатов тестов'
```

Для B:

```sh
cat /private/var/folders/pt/pg7fz4fd1_5fr07tng9zjbrw0000gn/T/usw-flow-activation-zv7x3cfb/usw.yaml
python3 -B /Users/leonidkim/Documents/projects/usw/skills/usw-run-flow/scripts/run_flow.py inspect /private/var/folders/pt/pg7fz4fd1_5fr07tng9zjbrw0000gn/T/usw-flow-activation-zv7x3cfb /private/var/folders/pt/pg7fz4fd1_5fr07tng9zjbrw0000gn/T/usw-flow-activation-zv7x3cfb/usw/flows test-evidence
```

Все команды завершились с exit code 0. `-B` исключал запись Python bytecode. Flow, Begin/Outcome, тесты и создание `RAN.txt` не выполнялись; записей в fixture не было. HANDOFF, backlog, specs, diff и соседние ресурсы не читались. Markdown использован только из ответов загрузчика. Native discovery хоста этой проверкой не подтверждается.
