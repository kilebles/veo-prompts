# veo-prompts

Генератор промптов для Google Veo 3 из текстовых документов.

## Установка

```bash
uv sync
```

## Настройка

Создать `.env` в корне:

```
ANTHROPIC_TOKEN=your-api-key
```

## Запуск

1. Положить `.docx` или `.txt` файл в `data/input/`
2. Запустить

```bash
uv run python -m app.main
```

3. Результат в `data/output/` в табличном формате CSV

## Архитектура

```
app/
  settings.py # конфиг, работа с файлами
  ai.py # запросы к Claude
  main.py # точка входа
data/
  input/ # исходные документы
  output/ # результаты (CSV)
```
