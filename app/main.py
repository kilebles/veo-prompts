from app.ai import generate_prompts
from app.settings import log, settings


def main(input_file: str, indices: list[int] | None = None) -> None:
    input_path = settings.input_file(input_file)
    paragraphs = settings.read_paragraphs(input_path)

    results = generate_prompts(paragraphs, indices)

    output_name = input_path.stem + "_prompts.txt"
    output_path = settings.output_file(output_name)

    lines = [f"{idx}. {prompt}" for idx, prompt in sorted(results.items())]
    output_path.write_text("\n\n".join(lines), encoding="utf-8")

    log.info(f"Saved to {output_path.name}")


if __name__ == "__main__":
    main("200. How People Kept Warm in Castles Without Fireplaces ENG.docx")
