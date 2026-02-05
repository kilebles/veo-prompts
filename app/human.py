import asyncio
import math
import random
import sys

from playwright.async_api import Page

MOD = "Meta" if sys.platform == "darwin" else "Control"


# --- Паузы ---

async def human_pause(min_s: float = 1.0, max_s: float = 3.0):
    """Человеческая пауза с редкими длинными задержками (раздумья)."""
    delay = random.uniform(min_s, max_s)
    # 5% шанс на длинную паузу (человек отвлёкся)
    if random.random() < 0.05:
        delay += random.uniform(3, 8)
    await asyncio.sleep(delay)


async def quick_sleep(min_s: float = 0.2, max_s: float = 0.6):
    """Короткая пауза между действиями."""
    await asyncio.sleep(random.uniform(min_s, max_s))


# --- Движение мыши ---

def _bezier_curve(t: float, p0: float, p1: float, p2: float, p3: float) -> float:
    """Кубическая кривая Безье для естественного движения."""
    return (
        (1 - t) ** 3 * p0 +
        3 * (1 - t) ** 2 * t * p1 +
        3 * (1 - t) * t ** 2 * p2 +
        t ** 3 * p3
    )


async def human_mouse_move(page: Page, target_x: float, target_y: float):
    """Плавное движение мыши по кривой Безье с человеческими характеристиками."""
    # Получаем текущую позицию мыши (или случайную стартовую)
    viewport = page.viewport_size
    if viewport:
        start_x = random.uniform(0, viewport["width"])
        start_y = random.uniform(0, viewport["height"])
    else:
        start_x, start_y = 500, 400

    # Контрольные точки для кривой Безье (создают естественный изгиб)
    distance = math.sqrt((target_x - start_x) ** 2 + (target_y - start_y) ** 2)
    offset = distance * random.uniform(0.1, 0.3)

    ctrl1_x = start_x + (target_x - start_x) * 0.3 + random.uniform(-offset, offset)
    ctrl1_y = start_y + (target_y - start_y) * 0.3 + random.uniform(-offset, offset)
    ctrl2_x = start_x + (target_x - start_x) * 0.7 + random.uniform(-offset, offset)
    ctrl2_y = start_y + (target_y - start_y) * 0.7 + random.uniform(-offset, offset)

    # Количество шагов зависит от расстояния
    steps = max(15, min(50, int(distance / 10)))

    for i in range(steps + 1):
        t = i / steps
        # Добавляем небольшое ускорение в начале и замедление в конце
        t = t * t * (3 - 2 * t)  # smoothstep

        x = _bezier_curve(t, start_x, ctrl1_x, ctrl2_x, target_x)
        y = _bezier_curve(t, start_y, ctrl1_y, ctrl2_y, target_y)

        # Микро-дрожание руки
        if i < steps:
            x += random.uniform(-1, 1)
            y += random.uniform(-1, 1)

        await page.mouse.move(x, y)

        # Вариативная скорость движения
        delay = random.uniform(0.005, 0.02)
        if random.random() < 0.1:
            delay += random.uniform(0.01, 0.03)  # Микро-пауза
        await asyncio.sleep(delay)


async def human_click(page: Page, locator):
    """Человеческий клик: движение к элементу + клик с вариацией."""
    box = await locator.bounding_box()
    if not box:
        await locator.click()
        return

    # Клик не точно в центр, а в случайную точку внутри элемента
    x = box["x"] + box["width"] * random.uniform(0.2, 0.8)
    y = box["y"] + box["height"] * random.uniform(0.3, 0.7)

    await human_mouse_move(page, x, y)
    await quick_sleep(0.05, 0.15)

    # Иногда двойное нажатие мыши (как у живого человека)
    if random.random() < 0.02:
        await page.mouse.down()
        await asyncio.sleep(random.uniform(0.01, 0.03))
        await page.mouse.up()
        await asyncio.sleep(random.uniform(0.05, 0.1))

    await page.mouse.click(x, y)


# --- Ввод текста ---

async def human_type(page: Page, text: str):
    """Посимвольный ввод с человеческими характеристиками."""
    for i, char in enumerate(text):
        # Базовая задержка между символами
        delay = random.uniform(0.03, 0.12)

        # Замедление на знаках препинания
        if char in ".,;:!?":
            delay += random.uniform(0.1, 0.25)

        # Замедление после пробела (начало нового слова)
        if i > 0 and text[i - 1] == " ":
            delay += random.uniform(0.05, 0.15)

        # Редкие паузы (человек думает)
        if random.random() < 0.03:
            delay += random.uniform(0.3, 1.0)

        # Редкая опечатка и исправление (2% шанс)
        if random.random() < 0.02 and char.isalpha():
            wrong_char = random.choice("asdfghjklqwertyuiopzxcvbnm")
            await page.keyboard.type(wrong_char, delay=0)
            await asyncio.sleep(random.uniform(0.1, 0.3))
            await page.keyboard.press("Backspace")
            await asyncio.sleep(random.uniform(0.05, 0.15))

        await page.keyboard.type(char, delay=0)
        await asyncio.sleep(delay)


async def human_type_field(page: Page, locator, text: str):
    """Клик в поле + человеческий ввод текста."""
    await human_click(page, locator)
    await quick_sleep(0.1, 0.3)
    await human_type(page, text)


# --- Имитация активности ---

async def simulate_reading(page: Page, duration: float = None):
    """Имитация чтения страницы: движения глаз = движения мыши."""
    if duration is None:
        duration = random.uniform(2, 5)

    viewport = page.viewport_size
    if not viewport:
        await asyncio.sleep(duration)
        return

    end_time = asyncio.get_event_loop().time() + duration

    while asyncio.get_event_loop().time() < end_time:
        # Случайное движение в зоне контента
        x = random.uniform(viewport["width"] * 0.2, viewport["width"] * 0.8)
        y = random.uniform(viewport["height"] * 0.2, viewport["height"] * 0.7)

        await page.mouse.move(x, y, steps=random.randint(5, 15))
        await asyncio.sleep(random.uniform(0.3, 1.5))


async def simulate_idle(page: Page):
    """Имитация бездействия с микро-движениями мыши."""
    viewport = page.viewport_size
    if not viewport:
        await asyncio.sleep(random.uniform(1, 3))
        return

    # Небольшое случайное движение (рука на мыши, но не активно)
    for _ in range(random.randint(1, 3)):
        current_x = random.uniform(100, viewport["width"] - 100)
        current_y = random.uniform(100, viewport["height"] - 100)

        # Микро-движение в пределах 20-50 пикселей
        offset_x = random.uniform(-30, 30)
        offset_y = random.uniform(-30, 30)

        await page.mouse.move(
            current_x + offset_x,
            current_y + offset_y,
            steps=random.randint(3, 8)
        )
        await asyncio.sleep(random.uniform(0.5, 2))


async def random_scroll(page: Page):
    """Случайный скролл страницы (как будто просматриваем контент)."""
    direction = random.choice([-1, 1])  # вверх или вниз
    amount = random.randint(100, 300) * direction

    # Плавный скролл несколькими шагами
    steps = random.randint(3, 6)
    for _ in range(steps):
        await page.mouse.wheel(0, amount // steps)
        await asyncio.sleep(random.uniform(0.05, 0.15))

    # Иногда скроллим обратно
    if random.random() < 0.3:
        await asyncio.sleep(random.uniform(0.5, 1))
        await page.mouse.wheel(0, -amount // 2)
