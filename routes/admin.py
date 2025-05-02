from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse
import psycopg2
from psycopg2.extras import DictCursor
import pandas as pd
import os

router = APIRouter()

templates = Jinja2Templates(directory="templates")

# connect to the database
conn = psycopg2.connect(
    host="localhost",
    dbname="postgres",
    user="postgres",
    password="postgres",
    port="5432"
)

cur = conn.cursor(cursor_factory=DictCursor)


def check_logged_in(request: Request):
    if "user_id" not in request.session:
        return False
    return True


@router.get("/users", response_class=HTMLResponse)
async def accounts(request: Request):
    if not check_logged_in(request):
        request.session["flash"] = {"message": "You are not logged in!", "category": "error"}
        return templates.TemplateResponse("login.html", {"request": request})

    cur.execute("SELECT id, username, role FROM users_ad ORDER BY id")
    users = cur.fetchall()
    df_users = pd.DataFrame(users, columns=["ID", "Username", "Role"])
    df_users = df_users.to_dict(orient="records")
    return templates.TemplateResponse("users.html", {"request": request, "df_users": df_users})


@router.get("/set_admin/{user_ID}")
async def set_admin(request: Request, user_ID: int):
    if request.session.get("role") == "admin":
        cur.execute("UPDATE users_ad SET role = 'admin' WHERE id = %s", (user_ID,))
        conn.commit()
        if request.session.get("id") == user_ID:
            request.session["role"] = "admin"
        return RedirectResponse(url="/admin/users", status_code=302)
    else:
        request.session["flash"] = {"message": "You are not an admin!", "category": "error"}
        return RedirectResponse(url="/auth/login", status_code=302)


@router.get("/set_production/{user_ID}")
async def set_production(request: Request, user_ID: int):
    if request.session.get("role") == "admin":
        cur.execute("UPDATE users_ad SET role = 'production' WHERE id = %s", (user_ID,))
        conn.commit()
        if request.session.get("id") == user_ID:
            request.session["role"] = "production"
        return RedirectResponse(url="/admin/users", status_code=302)
    else:
        request.session["flash"] = {"message": "You are not an admin!", "category": "error"}
        return RedirectResponse(url="/auth/login", status_code=302)


@router.get("/set_user/{user_ID}")
async def set_user(request: Request, user_ID: int):
    if request.session.get("role") == "admin":
        cur.execute("UPDATE users_ad SET role = 'user' WHERE id = %s", (user_ID,))
        conn.commit()
        if request.session.get("id") == user_ID:
            request.session["role"] = "user"
        return RedirectResponse(url="/admin/users", status_code=302)
    else:
        request.session["flash"] = {"message": "You are not an admin!", "category": "error"}
        return RedirectResponse(url="/auth/login", status_code=302)


@router.get("/delete_account/{user_ID}")
async def delete_account(request: Request, user_ID: int):
    cur.execute("DELETE FROM users_ad WHERE id = %s", (user_ID,))
    conn.commit()
    return RedirectResponse(url="/admin/users", status_code=302)
