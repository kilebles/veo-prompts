import logging
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE_DIR = Path(__file__).resolve().parent.parent
_LOG_DIR = _BASE_DIR / "logs"
_LOG_DIR.mkdir(exist_ok=True)
_LOG_FILE = _LOG_DIR / "app.log"

# Очищаем лог-файл при каждом запуске
_LOG_FILE.write_text("")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(_LOG_FILE, encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_token: str
    google_labs_url: str
    google_labs_login: str
    google_labs_password: str
    proxy: str = ""

    base_dir: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = base_dir / "data"
    input_dir: Path = data_dir / "input"
    output_dir: Path = data_dir / "output"

    def input_files(self, pattern: str = "*") -> list[Path]:
        return sorted(self.input_dir.glob(pattern))

    def input_file(self, name: str) -> Path:
        return self.input_dir / name

    def output_file(self, name: str) -> Path:
        return self.output_dir / name

    def read_paragraphs(self, file_path: Path) -> list[str]:
        log.info(f"Reading file: {file_path.name}")

        if file_path.suffix == ".docx":
            from docx import Document

            doc = Document(file_path)
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        else:
            text = file_path.read_text(encoding="utf-8")
            paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

        log.info(f"Parsed {len(paragraphs)} paragraphs")
        return paragraphs


settings = Settings()
