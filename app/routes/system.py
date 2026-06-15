from fastapi import APIRouter

from config.settings import settings

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/version")
def version() -> dict[str, str]:
    return {"app": settings.app_name, "version": settings.app_version}
