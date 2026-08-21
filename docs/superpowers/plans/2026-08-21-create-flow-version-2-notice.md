# Create-flow version-2 Notice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Сообщать о доступной нотации `version-2` перед первым черновиком нового flow без флага выбора стиля, не останавливая обычное создание.

**Architecture:** Поведение остаётся инструктивным: одна новая норма в OpenSpec, один behavior-сценарий и минимальная вставка в `usw-create-flow/SKILL.md`. Текущий checkout содержит незакоммиченные переводы в этом файле, поэтому feature-коммиты создаются в изолированном worktree; после проверки только новая вставка переносится в текущую рабочую копию без staging пользовательских изменений.

**Tech Stack:** Markdown skills, OpenSpec, JSON behavior scenarios, Python `unittest`, локальный Codex eval runner, POSIX installer.

---

### Task 1: Создать OpenSpec change

**Files:**
- Create: `openspec/changes/advertise-version-2-authoring/.openspec.yaml`
- Create: `openspec/changes/advertise-version-2-authoring/proposal.md`
- Create: `openspec/changes/advertise-version-2-authoring/design.md`
- Create: `openspec/changes/advertise-version-2-authoring/specs/markdown-flow-composition/spec.md`
- Create: `openspec/changes/advertise-version-2-authoring/tasks.md`

- [ ] **Step 1: Создать change**

Run:

```bash
openspec new change advertise-version-2-authoring
```

Expected: создан change со schema `spec-driven`.

- [ ] **Step 2: Записать planning artifacts**

В proposal зафиксировать одну проблему: новый flow без style selector молча
использует ordinary Markdown. В design зафиксировать неблокирующую подсказку
только для нового flow и отсутствие изменений формата или runtime.

Delta spec должна содержать полную изменённую норму:

```markdown
## MODIFIED Requirements

### Requirement: Обычный Markdown является форматом по умолчанию
`usw-create-flow` SHALL создавать обычный Markdown без version или DSL, если
пользователь явно не выбрал `-s` или `--structured`. Оба selectors SHALL выбирать
один и тот же authoring style `version-2`. Для нового flow без selector стиля
skill SHALL до первого черновика кратко сообщить о доступном `version-2`,
`--structured`, `-s` и маркерах `CALL`, `GATE`, `LOOP`, `PARALLEL`, пояснив,
что это подсказки для модели, а не исполняемый язык. Сообщение MUST NOT
останавливать ordinary authoring или требовать отдельного решения.

#### Scenario: Structured selector отсутствует
- **WHEN** пользователь создаёт flow без `-s` или `--structured`
- **THEN** сохранённый file является обычным Markdown

#### Scenario: Новый flow создаётся без selector стиля
- **WHEN** обе точки входа нового flow отсутствуют и пользователь не передал
  `-s` или `--structured`
- **THEN** до первого черновика skill сообщает о доступной нотации `version-2`
  и без ожидания ответа продолжает ordinary authoring

#### Scenario: Structured selector передан
- **WHEN** пользователь создаёт flow с любым structured selector
- **THEN** сохранённый file использует ту же readable convention `version-2`
```

Tasks должны отдельно перечислять delta, RED eval, skill edit, GREEN eval,
полную приёмку и переустановку.

- [ ] **Step 3: Проверить artifacts**

Run:

```bash
openspec validate advertise-version-2-authoring --strict
openspec status --change advertise-version-2-authoring --json
git diff --check
```

Expected: strict validation проходит; proposal, design, specs и tasks имеют
status `done`; whitespace errors отсутствуют.

- [ ] **Step 4: Commit**

```bash
git add openspec/changes/advertise-version-2-authoring
git commit -m "docs(openspec): propose version-2 notice"
```

### Task 2: Зафиксировать RED behavior-сценарий

**Files:**
- Create: `evals/scenarios/create-advertises-version-2/expect.json`
- Create: `evals/scenarios/create-advertises-version-2/flow.md`
- Create: `evals/scenarios/create-advertises-version-2/input.txt`
- Modify: `evals/scenarios/create-flat-edit/expect.json`

- [ ] **Step 1: Создать новый scenario**

`expect.json`:

```json
{
  "instructions": [
    "skills/usw-create-flow/SKILL.md",
    "skills/usw-create-flow/references/recipes.md"
  ],
  "expect": {
    "status_in": ["decision_required"],
    "external_action": "forbidden",
    "required_markers": ["version-2", "--structured", "-s"],
    "file_expectations": {
      ".usw/flows/meeting-checklist/FLOW.md": {"exists": false},
      ".usw/flows/meeting-checklist.md": {"exists": false}
    }
  },
  "notes": "The model must advertise the optional version-2 notation before proposing the first draft of a new flow, then wait for structure approval without writing. Markers prove discoverability but cannot prove their ordering relative to the draft; the transcript supplies that evidence."
}
```

`flow.md`:

```markdown
(Существующего flow с именем meeting-checklist нет.)
```

`input.txt`:

```text
Создай local flow meeting-checklist. Цель: перед встречей проверить повестку и
список участников. Готовых шагов нет. Решений по структуре в этом сообщении нет.
```

- [ ] **Step 2: Запретить подсказку при flat edit**

Добавить в верхний `expect` файла
`evals/scenarios/create-flat-edit/expect.json`:

```json
"forbidden_markers": ["version-2"]
```

Это проверяет ответ модели; существующая file expectation продолжает защищать
ordinary layout.

- [ ] **Step 3: Проверить загрузку scenario**

Run:

```bash
python3 -m unittest tests.test_eval_harness.ScenarioLoadingTests
```

Expected: PASS; marker contamination и JSON schema errors отсутствуют.

- [ ] **Step 4: Запустить baseline без новой skill-инструкции**

Run:

```bash
USW_EVAL_RUNNER='codex exec --sandbox workspace-write --skip-git-repo-check --ignore-user-config --ignore-rules --ephemeral -C {workdir} -' \
python3 evals/run_evals.py --scenario create-advertises-version-2 --runs 3 \
  --transcripts /tmp/usw-version-2-red
```

Expected: минимум один behavior failure из-за отсутствия одного или нескольких
required markers. Если все три запуска случайно проходят, изучить transcripts и
усилить scenario так, чтобы он измерял именно неблокирующее уведомление до
черновика, а не случайное упоминание selector.

- [ ] **Step 5: Commit RED scenario**

```bash
git add evals/scenarios/create-advertises-version-2 evals/scenarios/create-flat-edit/expect.json
git commit -m "test(evals): cover version-2 notice"
```

### Task 3: Добавить минимальную skill-инструкцию

**Files:**
- Modify: `skills/usw-create-flow/SKILL.md`
- Modify: `openspec/changes/advertise-version-2-authoring/tasks.md`

- [ ] **Step 1: Добавить правило перед проектированием от цели**

В начало раздела `## Проектирование от цели` добавить:

```markdown
Перед первым черновиком нового flow без `--structured` или `-s` один раз
сообщить:

> По умолчанию я создам обычный Markdown flow. Для сложных процессов доступен
> режим `--structured` (`-s`) — нотация `version-2` с явными вызовами,
> развилками, циклами и параллельными шагами (`CALL`, `GATE`, `LOOP`,
> `PARALLEL`). Это подсказки для модели, а не исполняемый язык. Если не
> попросите иначе, продолжу в обычном формате.

Не ждать ответа и продолжить обычный Markdown. Для существующего flow или явно
выбранного стиля подсказку не показывать. Если пользователь до записи просит
переключиться, прочитать `references/version-2.md` и заново показать черновик в
`version-2`.
```

Не менять frontmatter, `version-2.md`, recipes или invocation policy.

- [ ] **Step 2: Запустить GREEN behavior eval**

Run ту же команду с новым каталогом transcripts:

```bash
USW_EVAL_RUNNER='codex exec --sandbox workspace-write --skip-git-repo-check --ignore-user-config --ignore-rules --ephemeral -C {workdir} -' \
python3 evals/run_evals.py --scenario create-advertises-version-2 \
  --scenario create-flat-edit --runs 3 --transcripts /tmp/usw-version-2-green
```

Expected: оба scenario дают `3/3 [pass]`; новый flow не записан до согласования,
flat edit не получает уведомление и не мигрирует в `version-2`.

- [ ] **Step 3: Обновить tasks и commit**

Отметить delta, baseline и GREEN eval с фактическими rates.

```bash
git add skills/usw-create-flow/SKILL.md openspec/changes/advertise-version-2-authoring/tasks.md
git commit -m "feat(create-flow): advertise version-2"
```

### Task 4: Полная приёмка и установка

**Files:**
- Modify: `openspec/changes/advertise-version-2-authoring/tasks.md`
- Modify outside repo: installed USW skill copies via `install.sh --force`

- [ ] **Step 1: Запустить полную deterministic suite**

```bash
/Users/leonidkim/.local/share/uv/python/cpython-3.10-macos-aarch64-none/bin/python3.10 -m unittest discover -s tests
/Users/leonidkim/.local/share/uv/python/cpython-3.13-macos-aarch64-none/bin/python3.13 -m unittest discover -s tests
openspec validate --all --strict
git diff --check
```

Expected: 250 или больше tests проходят на обеих версиях Python; все OpenSpec
items проходят strict validation; whitespace errors отсутствуют.

- [ ] **Step 2: Зафиксировать acceptance**

Записать в tasks фактические test counts, OpenSpec totals и eval rates, затем:

```bash
git add openspec/changes/advertise-version-2-authoring/tasks.md
git commit -m "docs(acceptance): verify version-2 notice"
```

- [ ] **Step 3: Перенести только feature-вставку в текущий dirty checkout**

Применить согласованный блок к текущему
`skills/usw-create-flow/SKILL.md` поверх существующих переводов. Не stage и не
commit пользовательские изменения. Сверить feature-hunk с изолированным
worktree.

- [ ] **Step 4: Переустановить и сверить копии**

```bash
./install.sh --force
```

Затем сравнить шесть установленных USW skills для Qwen, Codex и Claude с
текущими исходниками, исключая `__pycache__`, `*.pyc` и `*.pyo`.

- [ ] **Step 5: Итоговый отчёт**

Сообщить feature branch и commit hashes, RED/GREEN rates, полную приёмку,
установленные targets и то, что текущие незакоммиченные переводы не попали в
feature-коммиты. Change оставить активным до отдельной проверки и архивации.
