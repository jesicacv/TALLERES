from fastapi.templating import Jinja2Templates

from config.settings import settings

templates = Jinja2Templates(directory="app/templates")


def base_context() -> dict[str, str]:
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
    }
