from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.datastructures import URL
import psycopg2
from email.message import EmailMessage
import smtplib
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
        status_message = "You are not logged in, please do so to access this page."
        return templates.TemplateResponse("login.html", {"request": request,
                                                         "status_message": status_message})

    cur.execute("SELECT id, username, role, email FROM users_ad ORDER BY id")
    users = cur.fetchall()
    df_users = pd.DataFrame(users, columns=["ID", "Username", "Role", "Email"])
    df_users = df_users.to_dict(orient="records")

    # převod flash hlášky do status_message pro toast
    flash = request.session.pop("flash", None)
    status_message = flash["message"] if flash else None

    return templates.TemplateResponse("users.html", {"request": request, "df_users": df_users,
                                                     "status_message": status_message})


@router.get("/set_admin/{user_ID}")
async def set_admin(request: Request, user_ID: int):
    if request.session.get("role") == "admin":
        cur.execute("UPDATE users_ad SET role = 'admin' WHERE id = %s", (user_ID,))
        conn.commit()
        if request.session.get("id") == user_ID:
            request.session["role"] = "admin"
        return RedirectResponse(url="/admin/users", status_code=302)
    else:
        status_message = "You are not an admin, you cannot access this page."
        return templates.TemplateResponse("home.html", {"request": request,
                                                        "status_message": status_message})


@router.get("/set_production/{user_ID}")
async def set_production(request: Request, user_ID: int):
    if request.session.get("role") == "admin":
        cur.execute("UPDATE users_ad SET role = 'production' WHERE id = %s", (user_ID,))
        conn.commit()
        if request.session.get("id") == user_ID:
            request.session["role"] = "production"
        return RedirectResponse(url="/admin/users", status_code=302)
    else:
        status_message = "You are not an admin, you cannot access this page."
        return templates.TemplateResponse("home.html", {"request": request,
                                                        "status_message": status_message})


@router.get("/set_user/{user_ID}")
async def set_user(request: Request, user_ID: int):
    if request.session.get("role") == "admin":
        cur.execute("UPDATE users_ad SET role = 'user' WHERE id = %s", (user_ID,))
        conn.commit()
        if request.session.get("id") == user_ID:
            request.session["role"] = "user"
        return RedirectResponse(url="/admin/users", status_code=302)
    else:
        status_message = "You are not an admin, you cannot access this page."
        return templates.TemplateResponse("home.html", {"request": request,
                                                        "status_message": status_message})


@router.get("/delete_account/{user_ID}")
async def delete_account(request: Request, user_ID: int):
    try:
        cur.execute("DELETE FROM users_ad WHERE id = %s", (user_ID,))
        conn.commit()
        request.session["flash"] = {"message": "User deleted successfully! ✅", "category": "success"}
    except Exception as e:
        conn.rollback()
        request.session["flash"] = {"message": f"Error deleting user: {e}", "category": "error"}

    return RedirectResponse(url="/admin/users", status_code=302)


@router.post("/add_user", response_class=HTMLResponse)
async def add_user(request: Request, email: str = Form(...)):
    if not check_logged_in(request):
        status_message = "You are not logged in, please do so to access this page."
        return templates.TemplateResponse("login.html", {"request": request,
                                                         "status_message": status_message})
    try:
        cur.execute("INSERT INTO users_ad (email) VALUES (%s)", (email,))
        conn.commit()
        msg = EmailMessage()
        msg['Subject'] = 'Your Access Has Been Approved – Doosan Bobcat Web Application'
        msg['From'] = 'webtest.mail@seznam.cz'
        msg['To'] = email
        msg.set_content(
            f"""Hello,
        
        Your access to the Doosan Bobcat internal web application has been successfully approved by the system administrator.
        
        You can now log in using your company credentials.
        
        Welcome aboard and thank you for supporting digital transformation at Bobcat!
        
        If you experience any issues, feel free to contact the administrator at patrik.brejla@doosan.com.
        
        Best regards,  
        Bobcat Automation Team"""
        )

        with smtplib.SMTP_SSL("smtp.seznam.cz", 465) as smtp:
            smtp.login("webtest.mail@seznam.cz", "Webtest-123")
            smtp.send_message(msg)

        status_message = "User added successfully! ✅"
    except Exception as e:
        conn.rollback()
        status_message = f"Error adding user: {e}"

    # ✅ znovu použijeme logiku z admin/users
    cur.execute("SELECT id, username, role, email FROM users_ad ORDER BY id")
    users = cur.fetchall()
    df_users = [{"ID": u[0], "Username": u[1], "Role": u[2], "Email": u[3]} for u in users]

    return templates.TemplateResponse("users.html", {
        "request": request,
        "df_users": df_users,
        "status_message": status_message
    })
