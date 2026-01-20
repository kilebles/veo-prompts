import csv

from app.ai import generate_prompts
from app.settings import log, settings


def main(indices: list[int] | None = None) -> None:
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


if __name__ == "__main__":
    main()
