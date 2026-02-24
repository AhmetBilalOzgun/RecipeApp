from fastapi import APIRouter, Depends, Path, HTTPException, Request
from starlette import status
from pydantic import BaseModel, Field
from fastapi.templating import Jinja2Templates
from app.models import Recipe
from sqlalchemy.orm import Session
from app.database import SessionLocal
from typing import Annotated
from ..routers.auth import get_current_user
from starlette.responses import RedirectResponse
from dotenv import load_dotenv
import google.generativeai as genai
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import markdown
from bs4 import BeautifulSoup

router = APIRouter(
    prefix="/recipe",
    tags=["Recipe"],
)

templates = Jinja2Templates(directory="app/templates")

class RecipeRequest(BaseModel):
    title: str = Field(min_length=3,max_length=100)
    description: str = Field(min_length=3,max_length=100)
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

@router.get("/recipe-page",status_code=status.HTTP_200_OK)
async def render_recipe_page(request: Request,db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()
        recipes= db.query(Recipe).filter(Recipe.user_id == user.get('id')).all()

        return templates.TemplateResponse("recipe.html", {"request": request,"recipes":recipes,"user":user})
    except:
        return redirect_to_login()
@router.get("/add-recipe-page",status_code=status.HTTP_200_OK)
async def render_add_recipe_page(request: Request):
    try:
        user = await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()
        return templates.TemplateResponse("add-recipe.html", {"request": request,"user":user})
    except:
        return redirect_to_login()

@router.get("/edit-recipe-page/{recipe_id}",status_code=status.HTTP_200_OK)
async def render_edit_recipe_page(request: Request,recipe_id: int,db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()

        recipe= db.query(Recipe).filter(Recipe.id == recipe_id).first()

        return templates.TemplateResponse("edit-recipe.html", {"request": request,"recipe":recipe,"user":user})
    except:
        return redirect_to_login()
@router.get("/")
async def get_all(user: user_dependency,db: db_dependency):
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db.query(Recipe).filter(Recipe.user_id == user.get('id')).all()

@router.get("/recipe/{recipe_id}",status_code=status.HTTP_200_OK)
async def get_by_id(user:user_dependency, db: db_dependency,recipe_id: int = Path(gt = 0)):
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).filter(Recipe.user_id == user.get('id')).first()
    if recipe is not None:
        return recipe
    else:
        raise HTTPException(status_code=404, detail="Not Found")

@router.post("/recipe",status_code=status.HTTP_201_CREATED)
async def create_recipe(user:user_dependency,db:db_dependency,recipe_request: RecipeRequest):
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    recipe = Recipe(**recipe_request.dict(), user_id = user.get('id'))
    recipe.description = create_recipe_with_gemini(recipe.description,recipe.title)
    db.add(recipe)
    db.commit()

@router.put("/recipe/{recipe_id}",status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user:user_dependency,db: db_dependency,recipe_request:RecipeRequest,recipe_id: int = Path(gt = 0)):
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).filter(Recipe.user_id == user.get('id')).first()
    if recipe is None:
        raise HTTPException(status_code=404, detail="Not Found")
    recipe.title = recipe_request.title
    recipe.description = recipe_request.description
    recipe.completed = recipe_request.completed
    db.add(recipe)
    db.commit()

@router.delete("/recipe/{recipe_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency,db: db_dependency,recipe_id: int = Path(gt = 0)):
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).filter(Recipe.user_id == user.get('id')).first()
    if recipe is not None:
        db.delete(recipe)
        db.commit()
    else:
        raise HTTPException(status_code=404, detail="Not Found")

def markdown_to_text(markdown_text):
    html = markdown.markdown(markdown_text)
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    return text


def create_recipe_with_gemini(recipe_string: str, recipe_title: str):
    load_dotenv()
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview")
    response = llm.invoke([
        HumanMessage(
            content="You are a world-class chef. I will provide you a recipe i want.What i want you to do is create a detailed recipe for my desired dish. my next message will be my desired dish and its title"),
        HumanMessage(content=recipe_title + recipe_string),
    ])

    # Gelen content bir liste ise (içinde type, text ve extras barındırıyorsa)
    # Sadece 'text' tipinde olan blokları birleştir
    if isinstance(response.content, list):
        extracted_text = "".join(
            [item.get("text", "") for item in response.content if isinstance(item, dict) and "text" in item])
    else:
        # Eğer zaten sadece string döndüyse olduğu gibi al
        extracted_text = response.content

    return markdown_to_text(extracted_text)

