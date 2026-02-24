from fastapi import APIRouter, Depends, Path, HTTPException, Request, Response
from starlette import status
from pydantic import BaseModel, Field
from fastapi.templating import Jinja2Templates
from ..models import Base, Todo
from sqlalchemy.orm import Session
from ..database import engine, SessionLocal
from typing import Annotated
from ..routers.auth import get_current_user
from starlette.responses import RedirectResponse
from dotenv import load_dotenv
import google.generativeai as genai
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
import markdown
from bs4 import BeautifulSoup

router = APIRouter(
    prefix="/todo",
    tags=["Todo"],
)

templates = Jinja2Templates(directory="app/templates")

class ToDoRequest(BaseModel):
    title: str = Field(min_length=3,max_length=100)
    description: str = Field(min_length=3,max_length=100)
    priority: int = Field(gt=0,lt=6)
    completed: bool = Field(default=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session,Depends(get_db)]
user_dependency = Annotated[Session,Depends(get_current_user)]

def redirect_to_login():
    redirect_response = RedirectResponse(url="/auth/login-page", status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie("access_token")
    return redirect_response

@router.get("/todo-page",status_code=status.HTTP_200_OK)
async def render_todo_page(request: Request,db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()
        todos= db.query(Todo).filter(Todo.user_id == user.get('id')).all()

        return templates.TemplateResponse("todo.html", {"request": request,"todos":todos,"user":user})
    except:
        return redirect_to_login()
@router.get("/add-todo-page",status_code=status.HTTP_200_OK)
async def render_add_todo_page(request: Request):
    try:
        user = await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()
        return templates.TemplateResponse("add-todo.html", {"request": request,"user":user})
    except:
        return redirect_to_login()

@router.get("/edit-todo-page/{todo_id}",status_code=status.HTTP_200_OK)
async def render_edit_todo_page(request: Request,todo_id: int,db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()

        todo= db.query(Todo).filter(Todo.id == todo_id).first()

        return templates.TemplateResponse("edit-todo.html", {"request": request,"todo":todo,"user":user})
    except:
        return redirect_to_login()
@router.get("/")
async def get_all(user: user_dependency,db: db_dependency):
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db.query(Todo).filter(Todo.user_id == user.get('id')).all()

@router.get("/todo/{todo_id}",status_code=status.HTTP_200_OK)
async def get_by_id(user:user_dependency, db: db_dependency,todo_id: int = Path(gt = 0)):
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.user_id == user.get('id')).first()
    if todo is not None:
        return todo
    else:
        raise HTTPException(status_code=404, detail="Not Found")

@router.post("/todo",status_code=status.HTTP_201_CREATED)
async def create_todo(user:user_dependency,db:db_dependency,todo_request: ToDoRequest):
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    todo = Todo(**todo_request.dict(), user_id = user.get('id'))
    todo.description = create_todo_with_gemini(todo.description)
    db.add(todo)
    db.commit()

@router.put("/todo/{todo_id}",status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user:user_dependency,db: db_dependency,todo_request:ToDoRequest,todo_id: int = Path(gt = 0)):
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.user_id == user.get('id')).first()
    if todo is None:
        raise HTTPException(status_code=404, detail="Not Found")
    todo.title = todo_request.title
    todo.description = create_todo_with_gemini(todo_request.description)
    todo.priority = todo_request.priority
    todo.completed = todo_request.completed
    db.add(todo)
    db.commit()

@router.delete("/todo/{todo_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency,db: db_dependency,todo_id: int = Path(gt = 0)):
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.user_id == user.get('id')).first()
    if todo is not None:
        db.delete(todo)
        db.commit()
    else:
        raise HTTPException(status_code=404, detail="Not Found")

def markdown_to_text(markdown_text):
    html = markdown.markdown(markdown_text)
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    return text


def create_todo_with_gemini(todo_string: str):
    load_dotenv()
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    llm = ChatGoogleGenerativeAI(model ="gemini-3-flash-preview")
    response= llm.invoke([
        HumanMessage(content="I will provide you a todo item to add my todo list.What i want you to do is create a longer and more comprehensive description of that todo item. my next message will be my todo"),
        HumanMessage(content=todo_string),
    ])
    return markdown_to_text(str(response.content))

