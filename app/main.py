import csv
import sys

from app.ai import generate_prompts
from app.settings import log, settings


def main(indices: list[int] | None = None, generate_videos: bool = False) -> None:
    input_files = settings.input_files()
    input_files = [f for f in input_files if f.name != ".gitkeep"]

    if not input_files:
        log.warning("No input files found")
        return

    input_path = input_files[0]
    paragraphs = settings.read_paragraphs(input_path)

    results = generate_prompts(paragraphs, indices)

    output_path = settings.output_file(input_path.stem + ".csv")

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["index", "paragraph", "prompt"])
        for idx, prompt in sorted(results.items()):
            writer.writerow([idx, paragraphs[idx - 1], prompt])

    log.info(f"Saved to {output_path.name}")

    # Запуск автоматизации генерации видео
    if generate_videos:
        log.info("Starting video generation automation...")
        from app.veo_automation import run_video_generation

        run_video_generation(output_path)


if __name__ == "__main__":
    generate_videos = "--generate-videos" in sys.argv or "-g" in sys.argv
    main(generate_videos=generate_videos)
