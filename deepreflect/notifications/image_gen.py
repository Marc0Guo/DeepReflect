"""Render the roast HTML page to a PNG using a headless Chromium browser."""
from __future__ import annotations

from pathlib import Path


async def html_to_png(html_path: Path, element_selector: str = "#report-page") -> bytes:
    """Screenshot *element_selector* inside html_path and return PNG bytes.

    Targets the #report-page div so the fixed export-bar is excluded.
    Raises RuntimeError with a helpful message if playwright/chromium are missing.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        raise RuntimeError(
            "playwright is not installed. Run: pip install playwright && playwright install chromium"
        ) from exc

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
        except Exception as exc:
            raise RuntimeError(
                "Chromium browser not found. Run: playwright install chromium"
            ) from exc

        page = await browser.new_page(viewport={"width": 960, "height": 1200})
        try:
            await page.goto(f"file://{html_path.resolve()}", wait_until="domcontentloaded")
            # Brief pause for web fonts / layout (file:// never reaches networkidle with external fonts).
            await page.wait_for_timeout(1200)
            element = await page.query_selector(element_selector)
            if element is None:
                # Fallback: screenshot the whole page body
                img = await page.screenshot(type="png", full_page=False)
            else:
                img = await element.screenshot(type="png")
        finally:
            await browser.close()

    return img
