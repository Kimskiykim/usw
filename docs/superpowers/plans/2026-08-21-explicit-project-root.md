# Explicit Project Root Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Сделать переданный корень открытого проекта единственным корнем USW без поиска родительского Git repository.

**Architecture:** Python entrypoints нормализуют и валидируют точный переданный каталог, но не обходят его родителей. Нормативные skills передают тот же явный root всем существующим скриптам; новый resolver или fallback не добавляется.

**Tech Stack:** Python 3.10+, `unittest`, Markdown skills, OpenSpec.

---

### Task 1: Exact root в Python entrypoints

**Files:**
- Modify: `tests/test_init_usw.py:261`
- Modify: `tests/test_handoff_state.py`
- Modify: `skills/usw-initialize-project/scripts/init_usw.py:245`
- Modify: `skills/usw-manage-handoff/scripts/handoff_state.py:131`

- [ ] **Step 1: Записать падающие regression tests**

Заменить старый init-сценарий проверкой точного вложенного каталога:

```python
def test_uses_exact_project_root_inside_parent_git_repo(self):
    with tempfile.TemporaryDirectory() as directory:
        parent = Path(directory)
        (parent / ".git").mkdir()
        project = parent / "src" / "feature"
        project.mkdir(parents=True)

        results = INIT_USW.initialize_usw(project)

        for path, _ in results:
            self.assertTrue(path.is_relative_to(project.resolve()))
        self.assertEqual(project.resolve() / "usw.yaml", results[0][0])
        self.assertFalse((parent / "usw.yaml").exists())
```

Добавить аналогичную проверку handoff helper:

```python
def test_project_root_is_exact_inside_parent_git_repo(self):
    with tempfile.TemporaryDirectory() as directory:
        parent = Path(directory)
        (parent / ".git").mkdir()
        project = parent / "nested"
        project.mkdir()

        self.assertEqual(project.resolve(), HANDOFF.find_project_root(project))
```

- [ ] **Step 2: Подтвердить RED**

Run:

```bash
python3 -m unittest \
  tests.test_init_usw.InitializeUswTests.test_uses_exact_project_root_inside_parent_git_repo \
  tests.test_handoff_state.HandoffStateTests.test_project_root_is_exact_inside_parent_git_repo
```

Expected: обе проверки FAIL, потому что текущие функции возвращают родительский каталог с `.git`.

- [ ] **Step 3: Реализовать минимальный exact-root contract**

Init helper должен только нормализовать и проверить аргумент:

```python
def find_project_root(start: Path) -> Path:
    """Return the exact supplied project directory."""
    start = start.expanduser().resolve()
    if not start.is_dir():
        raise NotADirectoryError(f"Project path is not a directory: {start}")
    return start
```

Handoff helper сохраняет свой наблюдаемый тип ошибки:

```python
def find_project_root(start: Path) -> Path:
    """Return the exact supplied project directory."""
    start = start.expanduser().resolve()
    if not start.is_dir():
        raise HandoffError("invalid_project", f"project is not a directory: {start}")
    return start
```

- [ ] **Step 4: Подтвердить GREEN**

Run ту же команду. Expected: `Ran 2 tests`, `OK`.

- [ ] **Step 5: Проверить затронутые модули**

Run:

```bash
python3 -m unittest tests.test_init_usw tests.test_handoff_state tests.test_end_to_end
```

Expected: `OK` без warnings и failures.

- [ ] **Step 6: Commit**

```bash
git add tests/test_init_usw.py tests/test_handoff_state.py \
  skills/usw-initialize-project/scripts/init_usw.py \
  skills/usw-manage-handoff/scripts/handoff_state.py
git commit -m "fix(runtime): use explicit project root"
```

### Task 2: Единый нормативный контракт

**Files:**
- Modify: `tests/test_atomic_skill_contracts.py`
- Modify: `skills/usw-initialize-project/SKILL.md`
- Modify: `skills/usw-initialize-project/references/llm-fallback.md`
- Modify: `skills/usw-manage-handoff/SKILL.md`
- Modify: `skills/usw-run-flow/SKILL.md`
- Modify: `skills/usw-find-flow/SKILL.md`
- Modify: `skills/usw-assess-flow/SKILL.md`
- Modify: `openspec/specs/workspace-configuration/spec.md`

- [ ] **Step 1: Добавить падающий tombstone test**

```python
def test_skills_do_not_discover_project_root_from_git(self):
    paths = (
        "skills/usw-initialize-project/SKILL.md",
        "skills/usw-initialize-project/references/llm-fallback.md",
        "skills/usw-manage-handoff/SKILL.md",
        "skills/usw-run-flow/SKILL.md",
        "skills/usw-find-flow/SKILL.md",
        "skills/usw-assess-flow/SKILL.md",
    )
    for relative in paths:
        content = (ROOT / relative).read_text(encoding="utf-8").lower()
        self.assertNotIn("ближайший git root", content, relative)
        self.assertNotIn("nearest git root", content, relative)
```

- [ ] **Step 2: Подтвердить RED**

Run:

```bash
python3 -m unittest \
  tests.test_atomic_skill_contracts.AtomicSkillContractTests.test_skills_do_not_discover_project_root_from_git
```

Expected: FAIL на существующих инструкциях Git-root discovery.

- [ ] **Step 3: Обновить нормативные тексты**

Во всех шести документах заменить ancestor discovery на один контракт:
использовать переданный корень открытого проекта буквально и не искать `.git`
или другой parent root. Не менять selectors, defaults, пути и permission
boundaries.

В `workspace-configuration/spec.md` добавить requirement и сценарий:

```markdown
### Requirement: Корень проекта задаётся явно
USW SHALL использовать переданный корень открытого проекта буквально и MUST
NOT выбирать другой workspace по наличию `.git` в родительском каталоге.

#### Scenario: Проект вложен в другой Git repository
- **WHEN** USW получает вложенную открытую папку как project root
- **THEN** configuration и managed paths разрешаются внутри неё без ancestor discovery
```

- [ ] **Step 4: Подтвердить GREEN и валидность OpenSpec**

Run:

```bash
python3 -m unittest tests.test_atomic_skill_contracts tests.test_package_layout
openspec validate --all --strict
```

Expected: тесты `OK`; OpenSpec — все items passed.

- [ ] **Step 5: Commit**

```bash
git add tests/test_atomic_skill_contracts.py \
  skills/usw-initialize-project/SKILL.md \
  skills/usw-initialize-project/references/llm-fallback.md \
  skills/usw-manage-handoff/SKILL.md \
  skills/usw-run-flow/SKILL.md \
  skills/usw-find-flow/SKILL.md \
  skills/usw-assess-flow/SKILL.md \
  openspec/specs/workspace-configuration/spec.md
git commit -m "docs(skills): require explicit project root"
```

### Task 3: Приёмка и установка

**Files:**
- No repository changes expected.
- Update installed copies under Qwen, Codex and Claude homes.

- [ ] **Step 1: Полная матрица Python**

Run:

```bash
/Users/leonidkim/.local/share/uv/python/cpython-3.10-macos-aarch64-none/bin/python3.10 \
  -m unittest discover -s tests -p 'test_*.py'
/Users/leonidkim/.local/share/uv/python/cpython-3.13-macos-aarch64-none/bin/python3.13 \
  -m unittest discover -s tests -p 'test_*.py'
```

Expected: одинаковое число tests, оба запуска `OK`.

- [ ] **Step 2: Статические проверки**

Run:

```bash
openspec validate --all --strict
git diff --check
```

Expected: OpenSpec без failures; `git diff --check` без вывода.

- [ ] **Step 3: Переустановить USW**

Run:

```bash
./install.sh all --force
```

Expected: шесть skills и шесть commands установлены для Qwen, Codex и Claude.

- [ ] **Step 4: Сверить установленные копии**

Сравнить рекурсивно шесть source skill directories и шесть command files со
всеми тремя installation roots. Expected: 36/36 exact byte matches.

- [ ] **Step 5: Финальное состояние**

Run:

```bash
git status --short --branch
```

Expected: чистая `dev/v2_hardening`.
