import time
import anthropic

from app.settings import log, settings

SYSTEM_PROMPT = """You are a film director, anthropologist, and visual historian creating cinematic video prompts for Google Veo 3 (fast mode). Your task is to generate 1 prompt in English from the provided paragraph."""

client = anthropic.Anthropic(api_key=settings.anthropic_token)


def generate_prompt(paragraph: str) -> str:
    """Generate a Veo 3 prompt from a paragraph"""
    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": paragraph}],
        )
        return response.content[0].text
    except anthropic.APIError as e:
        log.error(f"API error: {e}")
        return ""


def generate_prompts(
    paragraphs: list[str],
    indices: list[int] | None = None,
) -> dict[int, str]:
    """Generate Veo 3 prompts for selected paragraphs"""
    if indices is None:
        indices = list(range(1, len(paragraphs) + 1))

    results = {}
    total = len(indices)

    for count, idx in enumerate(indices, 1):
        if idx < 1 or idx > len(paragraphs):
            log.warning(f"Index {idx} out of range, skipping")
            continue

        log.info(f"Processing {count}/{total} (paragraph {idx})")
        prompt = generate_prompt(paragraphs[idx - 1])
        results[idx] = prompt

        if count < total:
            time.sleep(1)

    log.info(f"Generated {len([p for p in results.values() if p])} prompts")
    return results
