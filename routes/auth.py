from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2.extras import DictCursor
import os

router = APIRouter()

templates = Jinja2Templates(directory="templates")

# Připojení k databázi
conn = psycopg2.connect(
    host="localhost",
    dbname="postgres",
    user="postgres",
    password="postgres",
    port="5432"
)

cur = conn.cursor(cursor_factory=DictCursor)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    if user and check_password_hash(user["password"], password):
        request.session["user_id"] = user["id"]
        request.session["username"] = user["username"]
        request.session["role"] = user["role"]
        request.session["id"] = user["id"]
        return RedirectResponse(url="/main/home", status_code=302)
    else:
        request.session["flash"] = {"message": "Invalid credentials!", "category": "error"}
        return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
async def register_post(
    request: Request,
    name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...)
):
    cur.execute("SELECT * FROM users")
    rows = cur.fetchall()

    for row in rows:
        if row["username"] == username or row["email"] == email:
            request.session["flash"] = {"message": "Username already exists.", "category": "error"}
            return templates.TemplateResponse("register.html", {"request": request})

    hashed_password = generate_password_hash(password)
    cur.execute(
        "INSERT INTO users (name, username, password, email) VALUES (%s, %s, %s, %s)",
        (name, username, hashed_password, email)
    )
    conn.commit()

    request.session["flash"] = {"message": "Account created.", "category": "success"}
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/logout")
async def logout(request: Request):
    request.session.pop("user_id", None)
    request.session.pop("username", None)
    request.session.pop("role", None)
    request.session.pop("id", None)

    request.session["flash"] = {"message": "You've logged out successfully.", "category": "success"}
    return RedirectResponse(url="/auth/login", status_code=302)
