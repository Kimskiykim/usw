Контекст: адресная read-only проверка reviewer-а gate-7.1, не запуск flow
сначала. CLI-контракт уже передан исполнителем; пути ниже относительно текущей
папки fixture. Для этого сценария ответы CLI представлены снимком:

```json
{
  "schemaName": "decision-driven",
  "changeRoot": "planning/change",
  "applyRequires": ["decision"],
  "artifacts": [
    {"id": "brief", "status": "done", "requires": []},
    {"id": "constraints", "status": "done", "requires": ["brief"]},
    {"id": "decision", "status": "done", "requires": ["brief", "constraints"]}
  ],
  "artifactPaths": {
    "brief": {"resolvedOutputPath": "planning/change/planning/brief.md", "existingOutputPaths": ["planning/change/planning/brief.md"]},
    "constraints": {"resolvedOutputPath": "planning/change/checks/**/*.md", "existingOutputPaths": ["planning/change/checks/security/spec.md", "planning/change/checks/limits/spec.md"]},
    "decision": {"resolvedOutputPath": "planning/change/review/decision.md", "existingOutputPaths": ["planning/change/review/decision.md"]}
  }
}
```

Инструкции компонентов: brief фиксирует intent и scope; constraints содержит
оба обязательных документа security и limits; decision фиксирует решение,
согласованное с brief и обоими constraints. Компонентов задач, proposal и design
в схеме нет. Полный decision log: локально экспортировать отчёт в CSV по явной
команде пользователя; запрещена передача отчёта во внешние сервисы. Все файлы
доступны в fixture. Ничего не изменять и не создавать.
