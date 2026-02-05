import asyncio
import shutil
from datetime import datetime
from pathlib import Path

from playwright.async_api import (
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)
from playwright_stealth import Stealth

from app.auth import login
from app.human import (
    MOD,
    human_click,
    human_pause,
    quick_sleep,
    simulate_idle,
    simulate_reading,
)
from app.settings import log, settings


class VeoAutomation:
    """Автоматизация генерации видео через Google Veo 3."""

    MAX_QUEUE_SIZE = 5
    GENERATION_TIME = 120  # примерное время генерации в секундах
    BROWSER_STATE_DIR = settings.base_dir / ".browser_state"

    def __init__(self):
        self.playwright: Playwright | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.sent_count: int = 0
        self.generation_times: list[float] = []  # timestamps когда отправили

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self):
        """Запуск браузера и инициализация."""
        log.info("Starting browser...")

        self.BROWSER_STATE_DIR.mkdir(exist_ok=True)

        proxy_config = None
        if settings.proxy:
            proxy_parts = settings.proxy.split("@")
            credentials = proxy_parts[0].split(":")
            server = proxy_parts[1]
            proxy_config = {
                "server": f"http://{server}",
                "username": credentials[0],
                "password": credentials[1],
            }
            log.info(f"Using proxy: {server}")

        if not self.playwright:
            self.playwright = await async_playwright().start()

        launch_kwargs = {
            "user_data_dir": str(self.BROWSER_STATE_DIR),
            "headless": False,
            "args": [
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
                # Отключаем попапы
                "--disable-translate",  # перевод страницы
                "--disable-session-crashed-bubble",  # восстановление вкладок
                "--disable-infobars",  # инфобары сверху
                "--disable-features=TranslateUI",  # ещё раз перевод
                "--disable-popup-blocking",  # блокировка попапов
                "--no-first-run",  # первый запуск
                "--no-default-browser-check",  # проверка браузера по умолчанию
                "--disable-sync",  # синхронизация аккаунта
                "--disable-background-networking",
            ],
            "no_viewport": True,
            "locale": "en-US",
            "permissions": ["clipboard-read", "clipboard-write", "geolocation"],
            "geolocation": {"latitude": 37.7749, "longitude": -122.4194},
            "timezone_id": "America/Los_Angeles",
            "accept_downloads": True,
            "ignore_https_errors": True,
        }
        if proxy_config:
            launch_kwargs["proxy"] = proxy_config

        self.context = await self.playwright.chromium.launch_persistent_context(**launch_kwargs)

        # Устанавливаем разумный таймаут по умолчанию
        self.context.set_default_timeout(30000)

        self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()

        # Применяем stealth к странице
        stealth = Stealth()
        await stealth.apply_stealth_async(self.page)

        log.info("Browser started")

    async def close(self):
        """Закрытие браузера."""
        if self.context:
            try:
                await self.context.close()
            except Exception:
                pass
            self.context = None
            self.page = None
        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception:
                pass
            self.playwright = None
        log.info("Browser closed")

    # --- Error detection ---

    async def _has_error_toast(self) -> bool:
        """Проверка на toast-уведомление об ошибке (Sonner)."""
        try:
            toast = self.page.locator('[data-sonner-toast][data-visible="true"]:has(i:text("error"))')
            count = await toast.count()
            if count > 0:
                text_el = toast.first.locator('[data-title]')
                text = await text_el.inner_text() if await text_el.count() > 0 else "unknown"
                log.warning(f"Error toast detected: {text}")
                await self._save_error_screenshot()
                return True
        except Exception:
            pass
        return False

    async def _save_error_screenshot(self) -> None:
        """Сохранить скриншот ошибки в директорию логов."""
        try:
            log_dir = settings.base_dir / "logs"
            log_dir.mkdir(exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = log_dir / f"error_{ts}.png"
            await self.page.screenshot(path=str(path))
            log.error(f"Error screenshot saved: {path}")
        except Exception as e:
            log.error(f"Could not save error screenshot: {e}")

    async def _dismiss_error_toast(self) -> None:
        """Закрыть видимый toast с ошибкой."""
        try:
            toast = self.page.locator('[data-sonner-toast][data-visible="true"]:has(i:text("error"))')
            if await toast.count() > 0:
                close_btn = toast.first.locator('button')
                if await close_btn.count() > 0:
                    await close_btn.first.click()
                    await quick_sleep(0.3, 0.8)
                    log.info("Error toast dismissed")
        except Exception:
            pass

    # --- Error recovery ---

    async def _recover_from_error(self) -> None:
        """Очистить данные браузера, переоткрыть и вернуться в тот же flow."""
        # Сохраняем URL текущего flow
        flow_url = self.page.url if self.page else None
        log.warning(f"Recovering from error, flow URL: {flow_url}")

        # Закрываем браузер (но не playwright)
        if self.context:
            try:
                await self.context.close()
            except Exception:
                pass
            self.context = None
            self.page = None

        # Очищаем данные браузера
        if self.BROWSER_STATE_DIR.exists():
            shutil.rmtree(self.BROWSER_STATE_DIR, ignore_errors=True)
            log.info("Browser data cleared")

        await asyncio.sleep(3)

        # Переоткрываем браузер
        await self.start()

        # Логинимся и возвращаемся в тот же flow
        await login(self.page, return_url=flow_url)

        await self.set_outputs_per_prompt(1)
        log.info("Recovery complete")

    # --- Queue ---

    def _get_active_generations(self) -> int:
        """Получить количество активных генераций по времени отправки."""
        import time
        now = time.time()
        # Убираем те что уже должны были завершиться
        self.generation_times = [t for t in self.generation_times if now - t < self.GENERATION_TIME]
        return len(self.generation_times)

    def _add_generation(self):
        """Зарегистрировать новую генерацию."""
        import time
        self.generation_times.append(time.time())

    async def wait_for_queue_space(self):
        """Ожидание места в очереди."""
        while True:
            active = self._get_active_generations()
            log.info(f"Queue: {active}/{self.MAX_QUEUE_SIZE}")

            if active < self.MAX_QUEUE_SIZE:
                return

            log.info("Queue full, waiting 30s...")
            await asyncio.sleep(30)

    async def set_outputs_per_prompt(self, count: int = 1):
        """Установка количества outputs per prompt через попап настроек."""
        log.info(f"Setting outputs per prompt to {count}...")

        try:
            await simulate_idle(self.page)

            settings_button = self.page.locator('button:has(i:text("tune"))').first
            await settings_button.wait_for(state="visible", timeout=10000)
            await human_click(self.page, settings_button)
            await quick_sleep(0.5, 1)

            combobox = self.page.locator('button[role="combobox"]:has(span:text("Outputs per prompt"))').first
            await human_click(self.page, combobox)
            await quick_sleep(0.3, 0.6)

            option = self.page.locator(f'[role="option"]:has-text("{count}")').first
            await human_click(self.page, option)
            await quick_sleep(0.2, 0.4)

            await self.page.keyboard.press("Escape")
            log.info(f"Outputs per prompt set to {count}")

        except Exception as e:
            log.warning(f"Could not set outputs per prompt: {e}")

    # --- Video generation ---

    async def generate_video(self, prompt: str, index: int):
        """Отправка одного промпта на генерацию."""
        log.info(f"Generating video {index} with prompt: {prompt[:50]}...")

        # Имитация просмотра страницы перед действием
        await simulate_reading(self.page, duration=1.5)

        prompt_field = self.page.locator('#PINHOLE_TEXT_AREA_ELEMENT_ID')
        await prompt_field.wait_for(state="visible", timeout=10000)

        # Человеческий клик в поле ввода
        await human_click(self.page, prompt_field)
        await quick_sleep(0.2, 0.4)

        # Очистка поля
        await self.page.keyboard.press(f"{MOD}+A")
        await quick_sleep(0.05, 0.15)
        await self.page.keyboard.press("Backspace")
        await quick_sleep(0.2, 0.4)

        # Вставка текста через буфер (быстрее чем печатать длинный промпт)
        await self.page.evaluate("text => navigator.clipboard.writeText(text)", prompt)
        await quick_sleep(0.1, 0.3)
        await self.page.keyboard.press(f"{MOD}+V")

        # Пауза как будто проверяем текст
        await human_pause(1.5, 3)

        # Отправка
        await self.page.keyboard.press("Enter")
        self.sent_count += 1
        log.info(f"Video {index} generation started ({self.sent_count} sent total)")

    async def generate_videos_batch(self, prompts: list[tuple[int, str]]):
        """Генерация пакета видео."""
        total = len(prompts)
        log.info(f"Starting batch: {total} videos")

        await login(self.page)
        await self.set_outputs_per_prompt(1)

        i = 0
        while i < total:
            index, prompt = prompts[i]

            try:
                # Ждём место в очереди
                await self.wait_for_queue_space()

                log.info(f"Video {i + 1}/{total} (index: {index})")
                await self.generate_video(prompt, index)

                # Ждём 3 секунды и проверяем на ошибку
                await asyncio.sleep(3)

                if await self._has_error_toast():
                    log.error(f"Error after video {index}, recovering...")
                    await self._dismiss_error_toast()
                    await self._recover_from_error()
                    continue

                # Пауза между генерациями
                await human_pause(2, 4)

                i += 1

            except Exception as e:
                log.error(f"Exception on video {index}: {e}")
                try:
                    await self._recover_from_error()
                except Exception as re:
                    log.error(f"Recovery failed: {re}, waiting 30s...")
                    await asyncio.sleep(30)
                # не инкрементируем — повторим этот промпт

        log.info("Batch generation completed")


async def generate_videos_from_csv(csv_path: Path):
    """Загрузка промптов из CSV и запуск генерации."""
    import csv

    log.info(f"Reading prompts from {csv_path.name}")

    prompts = []
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            index = int(row["index"])
            prompt = row["prompt"]
            prompts.append((index, prompt))

    log.info(f"Loaded {len(prompts)} prompts")

    async with VeoAutomation() as automation:
        await automation.generate_videos_batch(prompts)


def run_video_generation(csv_path: Path):
    """Синхронная обертка для запуска генерации видео."""
    asyncio.run(generate_videos_from_csv(csv_path))
