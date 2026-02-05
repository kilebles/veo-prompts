"""
Скрипт для автоматического запуска генерации видео в Veo,
если CSV файл с промптами уже существует.
"""

import sys

from pathlib import Path
from app.settings import log, settings
from app.veo_automation import run_video_generation


def find_latest_csv() -> Path | None:
    """Найти последний CSV файл в директории output."""
    csv_files = list(settings.output_dir.glob("*.csv"))

    if not csv_files:
        return None

    csv_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return csv_files[0]


def main():
    """Главная функция."""
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])

        if not csv_path.exists():
            log.error(f"CSV file not found: {csv_path}")
            sys.exit(1)

        if not csv_path.suffix == ".csv":
            log.error(f"File is not a CSV: {csv_path}")
            sys.exit(1)

        log.info(f"Using specified CSV file: {csv_path.name}")
    else:
        csv_path = find_latest_csv()

        if not csv_path:
            log.error("No CSV files found in output directory")
            log.info("Please run 'python -m app.main' first to generate prompts")
            sys.exit(1)

        log.info(f"Found CSV file: {csv_path.name}")

    log.info("Starting Veo automation...")

    try:
        run_video_generation(csv_path)
        log.info("✓ Video generation completed successfully")
    except KeyboardInterrupt:
        log.warning("Video generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        log.error(f"Video generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
