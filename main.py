from urllib.request import Request
from starlette import status
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

from .models import Base

from .database import engine
from .routers.auth import router as auth_router
from .routers.todo import router as todo_router
import os

script_dir = os.path.dirname(__file__)
st_abs_file_path = os.path.join(script_dir, "static/")
app = FastAPI()
app.mount("/static", StaticFiles(directory=st_abs_file_path), name="static")
app.include_router(auth_router)
app.include_router(todo_router)

@app.get("/")
async def read_root(request: Request):
    return RedirectResponse(url= "/todo/todo-page")


Base.metadata.create_all(bind=engine)

