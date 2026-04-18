"""
Playwright web automation skill
Provides web automation capabilities based on Playwright
"""
import logging
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.skills.base import BaseSkill, SkillExecutionError, SkillOutput

logger = logging.getLogger(__name__)


class PlaywrightParams(BaseModel):
    """Playwright skill parameters"""
    action: str = Field(..., description="Action type: navigate | click | fill | screenshot | extract_text")
    url: Optional[str] = Field(None, description="Target URL")
    selector: Optional[str] = Field(None, description="CSS selector")
    value: Optional[str] = Field(None, description="Fill value")
    headless: bool = Field(default=True, description="Whether to use headless mode")
    timeout: int = Field(default=30000, description="Timeout in milliseconds")


class PlaywrightSkill(BaseSkill):
    """
    Playwright web automation skill
    Supports web navigation, clicking, form filling, screenshots, and text extraction
    """

    name = "playwright_web"
    description = "Web automation via Playwright: page navigation, element clicking, form filling, screenshots, text extraction"
    require_human_approval = False

    async def execute(self, params: Dict[str, Any]) -> SkillOutput:
        """Execute a Playwright operation"""
        try:
            pw_params = PlaywrightParams(**params)
        except Exception as e:
            return SkillOutput(success=False, error_message=f"Parameter validation failed: {e}")

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return SkillOutput(success=False, error_message="Playwright not installed. Please run: pip install playwright && playwright install")

        action = pw_params.action.lower()
        self.logger.info(f"Playwright action={action}, url={pw_params.url}")

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=pw_params.headless)
                page = await browser.new_page()

                result = None

                if action == "navigate":
                    await page.goto(pw_params.url, timeout=pw_params.timeout)
                    result = {"title": await page.title(), "url": page.url}

                elif action == "click":
                    if pw_params.url:
                        await page.goto(pw_params.url, timeout=pw_params.timeout)
                    await page.click(pw_params.selector, timeout=pw_params.timeout)
                    result = {"clicked": pw_params.selector}

                elif action == "fill":
                    if pw_params.url:
                        await page.goto(pw_params.url, timeout=pw_params.timeout)
                    await page.fill(pw_params.selector, pw_params.value or "")
                    result = {"filled": pw_params.selector, "value": pw_params.value}

                elif action == "screenshot":
                    if pw_params.url:
                        await page.goto(pw_params.url, timeout=pw_params.timeout)
                    screenshot_bytes = await page.screenshot(full_page=True)
                    import base64
                    result = {
                        "screenshot_base64": base64.b64encode(screenshot_bytes).decode(),
                        "size_bytes": len(screenshot_bytes),
                    }

                elif action == "extract_text":
                    if pw_params.url:
                        await page.goto(pw_params.url, timeout=pw_params.timeout)
                    selector = pw_params.selector or "body"
                    text = await page.inner_text(selector)
                    result = {"text": text[:5000], "selector": selector}   # limit text length

                else:
                    await browser.close()
                    return SkillOutput(success=False, error_message=f"Unsupported operation: {action}")

                await browser.close()
                return SkillOutput(success=True, data=result)

        except Exception as e:
            raise SkillExecutionError(self.name, f"Playwright operation failed: {e}", retriable=False)

    def get_tool_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["navigate", "click", "fill", "screenshot", "extract_text"],
                            "description": "Playwright operation type",
                        },
                        "url": {"type": "string", "description": "Target webpage URL"},
                        "selector": {"type": "string", "description": "CSS selector"},
                        "value": {"type": "string", "description": "Value to fill"},
                        "headless": {"type": "boolean", "description": "Whether to use headless mode, default true"},
                    },
                    "required": ["action"],
                },
            },
        }
