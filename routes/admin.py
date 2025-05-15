from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from routes.auth import get_current_user, User
import psycopg2
from psycopg2.extras import DictCursor
import pandas as pd
from email.message import EmailMessage
import smtplib

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# DB připojení
conn = psycopg2.connect(
    host="localhost",
    dbname="postgres",
    user="postgres",
    password="postgres",
    port="5432"
)
cur = conn.cursor(cursor_factory=DictCursor)

"""
Všechny následující funkce může vykonávat pouze uživatel s rolí admin.

English:
All the following functions can only be performed by a user with the admin role.
"""


@router.get("/users", response_class=HTMLResponse)
async def accounts(request: Request, user: User = Depends(get_current_user)):
    """
    Zobrazí seznam uživatelů a jejich rolí.

    English:
    Displays a list of users and their roles.
    """

    if user.role != "admin":
        return templates.TemplateResponse("home.html", {
            "request": request,
            "status_message": "You are not an admin, you cannot access this page."
        })

    cur.execute("SELECT id, username, role, email FROM users_ad ORDER BY id")
    users = cur.fetchall()
    df_users = pd.DataFrame(users, columns=["ID", "Username", "Role", "Email"]).to_dict(orient="records")

    return templates.TemplateResponse("users.html", {
        "request": request,
        "df_users": df_users,
        "status_message": request.query_params.get("status_message"),
        "username": user.username,
        "role": user.role
    })


def update_user_role(user_id: int, role: str):
    """
    Aktualizuje roli uživatele v databázi.

    English:
    Updates the user's role in the database.
    """

    cur.execute("UPDATE users_ad SET role = %s WHERE id = %s", (role, user_id))
    conn.commit()


@router.get("/set_admin/{user_ID}")
async def set_admin(user_ID: int, user: User = Depends(get_current_user)):
    """
    Nastaví uživateli roli admin.

    English:
    Sets the user's role to admin.
    """

    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can perform this action")
    update_user_role(user_ID, "admin")
    return RedirectResponse(url="/admin/users", status_code=302)


@router.get("/set_production/{user_ID}")
async def set_production(user_ID: int, user: User = Depends(get_current_user)):
    """
    Nastaví uživateli roli production.

    English:
    Sets the user's role to production.
    """

    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can perform this action")
    update_user_role(user_ID, "production")
    return RedirectResponse(url="/admin/users", status_code=302)


@router.get("/set_user/{user_ID}")
async def set_user(user_ID: int, user: User = Depends(get_current_user)):
    """
    Nastaví uživateli roli user.

    English:
    Sets the user's role to user.
    """

    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can perform this action")
    update_user_role(user_ID, "user")
    return RedirectResponse(url="/admin/users", status_code=302)


@router.get("/delete_account/{user_ID}")
async def delete_account(user_ID: int, user: User = Depends(get_current_user)):
    """
    Smaže uživatelský účet.

    English:
    Deletes the user account.
    """

    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can perform this action")
    try:
        cur.execute("DELETE FROM users_ad WHERE id = %s", (user_ID,))
        conn.commit()
        msg = "User deleted successfully ✅"
    except Exception as e:
        conn.rollback()
        msg = f"Error deleting user: {e}"
    return RedirectResponse(url=f"/admin/users", status_code=302)


@router.post("/add_user", response_class=HTMLResponse)
async def add_user(request: Request, email: str = Form(...), user: User = Depends(get_current_user)):
    """
    Přidá uživatele do databáze a odešle mu email s potvrzením.

    English:
    Adds a user to the database and sends them a confirmation email.
    """

    if user.role != "admin":
        return templates.TemplateResponse("home.html", {
            "request": request,
            "status_message": "You are not an admin, you cannot add users."
        })

    try:
        cur.execute("INSERT INTO users_ad (email) VALUES (%s)", (email,))
        conn.commit()

        msg = EmailMessage()
        msg["Subject"] = "Your Access Has Been Approved – Doosan Bobcat Web Application"
        msg["From"] = "webtest.mail@seznam.cz"
        msg["To"] = email
        msg.set_content(f"""Hello,
        
        Your access to the Doosan Bobcat internal web application has been successfully approved by the system administrator.
        
        You can now log in using your company credentials.
        
        Welcome aboard and thank you for supporting digital transformation at Bobcat!
        
        If you experience any issues, feel free to contact the administrator at patrik.brejla@doosan.com.
        
        Best regards,  
        Bobcat Automation Team""")

        with smtplib.SMTP_SSL("smtp.seznam.cz", 465) as smtp:
            smtp.login("webtest.mail@seznam.cz", "Webtest-123")
            smtp.send_message(msg)

        msg = "User added successfully ✅"
    except Exception as e:
        conn.rollback()
        msg = f"Error adding user: {e}"

    return RedirectResponse(url=f"/admin/users", status_code=302)
