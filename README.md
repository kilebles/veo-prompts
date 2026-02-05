# Veo Video Generation Automation

Автоматизация генерации видео через Google Veo 3 с использованием AI-генерации промптов.

## Структура проекта

```
veo-prompts/
├── app/
│   ├── ai.py                 # Генерация промптов через Claude API
│   ├── main.py               # Основной скрипт для генерации промптов
│   ├── settings.py           # Настройки и конфигурация
│   └── veo_automation.py     # Автоматизация браузера для Veo
├── data/
│   ├── input/                # Входные файлы (.txt, .docx)
│   └── output/               # Выходные CSV файлы и видео
├── run_veo_automation.py     # Запуск автоматизации Veo
└── .env                      # Переменные окружения
```

## Установка

1. Клонировать репозиторий
2. Установить зависимости:
```bash
uv sync
```

3. Установить Playwright браузеры:
```bash
playwright install chromium
```

4. Создать `.env` файл со следующими переменными:
```env
ANTHROPIC_TOKEN=your_anthropic_api_key
GOOGLE_LABS_URL=https://labs.google/fx/tools/video-fx
GOOGLE_LABS_LOGIN=your_google_email
GOOGLE_LABS_PASSWORD=your_google_password
```

## Использование

### Вариант 1: Генерация промптов + автоматизация Veo

1. Поместить входной файл (.txt или .docx) в `data/input/`
2. Запустить генерацию промптов и видео:
```bash
python -m app.main --generate-videos
```

### Вариант 2: Только генерация промптов

```bash
python -m app.main
```

Результат сохранится в `data/output/filename.csv`

### Вариант 3: Только автоматизация Veo (если CSV уже есть)

Использовать последний CSV файл:
```bash
python run_veo_automation.py
```

Или указать конкретный файл:
```bash
python run_veo_automation.py "data/output/your_file.csv"
```

## Формат CSV

CSV файл содержит колонки:
- `index` - порядковый номер
- `paragraph` - исходный текст параграфа
- `prompt` - сгенерированный промпт для Veo

## Особенности

- Автоматическая авторизация в Google Labs
- Управление очередью генерации (макс. 5 видео одновременно)
- Автоматическое скачивание готовых видео
- Обработка ошибок и rate limits
- Headless режим браузера для визуального контроля
