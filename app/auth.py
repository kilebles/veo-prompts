from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from app.human import human_click, human_pause, human_type_field, quick_sleep, simulate_reading
from app.settings import log, settings


async def login(page: Page, return_url: str | None = None) -> None:
    """Авторизация через Google.

    Порядок:
    1. Открываем URL → лендинг с "Create with Flow"
    2. Кликаем "Create with Flow" → появляется форма логина Google
    3. Вводим логин/пароль
    4. После логина → кликаем "New project"
    """
    log.info("Starting login...")
    log.info(f"Opening {settings.google_labs_url}")

    await page.goto(settings.google_labs_url)
    await human_pause(2, 4)

    log.info(f"Page loaded, URL: {page.url}")
    await simulate_reading(page, duration=1.5)

    new_project_btn = page.locator('button:has(i:text("add_2"))').first
    create_btn = page.locator(
        'button:has(span:text("Create with Flow")), button:has(span:text("Tạo bằng Flow"))'
    ).first

    # 1. Проверяем — может уже залогинены (есть "New project")
    log.info("Checking if already logged in...")
    try:
        await new_project_btn.wait_for(state="visible", timeout=5000)
        log.info("Already logged in — found 'New project' button")
        if return_url:
            log.info(f"Returning to flow: {return_url}")
            await page.goto(return_url)
            await _wait_for_project_page(page)
        else:
            log.info("Clicking 'New project'...")
            await human_click(page, new_project_btn)
            await _wait_for_project_page(page)
        return
    except PlaywrightTimeout:
        pass

    # 2. Кликаем "Create with Flow" — это откроет форму логина
    try:
        await create_btn.wait_for(state="visible", timeout=10000)
        log.info("Clicking 'Create with Flow'...")
        await human_click(page, create_btn)
        await human_pause(2, 4)
    except PlaywrightTimeout:
        log.warning("'Create with Flow' button not found")

    # 3. Теперь должна появиться форма логина Google
    email_field = page.locator('input[type="email"]')
    try:
        await email_field.wait_for(state="visible", timeout=10000)
        log.info("Google login form appeared, entering credentials...")
        await _do_google_login(page)
        await page.wait_for_url("**/flow**", timeout=30000)
        log.info("Login successful")
        await human_pause(2, 4)
        await simulate_reading(page, duration=2)
    except PlaywrightTimeout:
        log.info("No login form — might be already logged in")

    # 4. После логина — кликаем "New project" или переходим по return_url
    if return_url:
        log.info(f"Returning to flow: {return_url}")
        await page.goto(return_url)
        await _wait_for_project_page(page)
        return

    try:
        await new_project_btn.wait_for(state="visible", timeout=30000)
        log.info("Clicking 'New project'...")
        await human_click(page, new_project_btn)
        await _wait_for_project_page(page)
    except PlaywrightTimeout:
        log.error("'New project' button not found after login")
        raise


async def _do_google_login(page: Page) -> None:
    """Ввод логина и пароля Google."""
    await simulate_reading(page, duration=1)

    email_field = page.locator('input[type="email"]')
    await email_field.wait_for(state="visible", timeout=10000)
    await quick_sleep(0.3, 0.6)
    await human_type_field(page, email_field, settings.google_labs_login)
    await human_pause(0.5, 1)
    await page.keyboard.press("Enter")
    await human_pause(2, 3)

    password_field = page.locator('input[type="password"]')
    await password_field.wait_for(state="visible", timeout=10000)
    await quick_sleep(0.3, 0.6)
    await human_type_field(page, password_field, settings.google_labs_password)
    await human_pause(0.5, 1)
    await page.keyboard.press("Enter")


async def _wait_for_project_page(page: Page) -> None:
    """Ждём загрузки страницы проекта."""
    log.info("Waiting for project page...")
    prompt_field = page.locator('#PINHOLE_TEXT_AREA_ELEMENT_ID')
    await prompt_field.wait_for(state="visible", timeout=30000)
    await simulate_reading(page, duration=1.5)
    log.info("Project page loaded")
