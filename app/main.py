from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.core.web_auth import (
    LOGIN_PATH,
    PASSWORD_CHANGE_PATH,
    NotAuthenticatedError,
    PasswordChangeRequiredError,
)
from app.routes.auth import router as auth_router
from app.routes.maestros import router as maestros_router
from app.routes.movimientos import router as movimientos_router
from app.routes.seguridad import router as seguridad_router
from app.routes.system import router as system_router
from app.routes.web import router as web_router
from app.routes.web_auth import router as web_auth_router
from config.settings import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


def _auth_redirect(request: Request, location: str) -> Response:
    # En peticiones HTMX usamos HX-Redirect para que el navegador navegue de verdad
    # (en vez de inyectar la pagina de login dentro de un fragmento).
    if request.headers.get("HX-Request"):
        return Response(status_code=204, headers={"HX-Redirect": location})
    return RedirectResponse(location, status_code=303)


@app.exception_handler(NotAuthenticatedError)
async def _not_authenticated_handler(request: Request, exc: NotAuthenticatedError) -> Response:
    return _auth_redirect(request, LOGIN_PATH)


@app.exception_handler(PasswordChangeRequiredError)
async def _password_change_handler(request: Request, exc: PasswordChangeRequiredError) -> Response:
    return _auth_redirect(request, PASSWORD_CHANGE_PATH)


app.include_router(web_auth_router)
app.include_router(web_router)
app.include_router(auth_router)
app.include_router(maestros_router)
app.include_router(movimientos_router)
app.include_router(seguridad_router)
app.include_router(system_router)


@app.get("/api")
def api_root() -> dict[str, str]:
    return {"message": "API Taller Mecanico activa"}

