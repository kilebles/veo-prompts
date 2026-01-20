from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_token: str

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


settings = Settings()
