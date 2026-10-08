# Baseline: старые инструкции

Дата: 2026-10-09. Модель получила только два исходных SKILL.md и их metadata.
Candidate loading не считался вызовом. Runtime и Python не запускались.

| Запрос | Фактический результат |
| --- | --- |
| Найди flow для проверки результатов тестов | find не активируется: нет вызова usw-find-flow |
| Оцени flow test-evidence | assess не активируется: нет вызова usw-assess-flow |
| Проверь код в src/ | Ни find, ни assess |
| У нас есть flow test-evidence, но сейчас просто обсуждаем сроки | Ни find, ни assess |
| Оцени flow, без другого контекста | Нужен вопрос об имени; нет вызова skill |

Raw основание агента: оба SKILL.md требуют «только при явном вызове»
соответствующего skill, оба agents/openai.yaml задают allow_implicit_invocation:
false. Загрузка кандидата этого ограничения не снимает.

Это bounded prompt acceptance check, не native discovery и не runtime observation.
