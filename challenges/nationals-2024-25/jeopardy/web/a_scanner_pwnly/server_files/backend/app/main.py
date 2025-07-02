import sys
import traceback
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.database import User
from app.routes.scanner import router as scanner_router
from app.schemas import UserCreate, UserRead, UserUpdate
from app.users import auth_backend, current_active_user, fastapi_users

app = FastAPI()


app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
app.include_router(scanner_router, prefix="/scanner", tags=["scanner"])


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    exc_info = sys.exc_info()
    exception = "".join(traceback.format_exception(*exc_info))
    return JSONResponse({"error": exception}, status_code=500)


@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(str(exc), status_code=400)


@app.get("/authenticated-route")
async def authenticated_route(
    user: Annotated[User, Depends(current_active_user)],
):
    return {"message": f"Hello {user.email}!"}


@app.get("/")
async def index():
    return {"message": "Hello, world!"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1337",
        "https://localhost:1337",
        "http://badgescan.valverde.vote:1337",
        "https://badgescan.valverde.vote:1337",
        "http://localhost:8000",
        "https://localhost:8000",
        "http://api.badgescan.valverde.vote:8000",
        "https://api.badgescan.valverde.vote:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Cookie", "Content-Type"],
)
