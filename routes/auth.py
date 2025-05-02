from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ldap3 import Server, Connection, ALL, NTLM
from email.message import EmailMessage
import smtplib
import psycopg2
from psycopg2.extras import DictCursor

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

# LDAP parametry
LDAP_SERVER = 'ldaps://corp.doosan.com'
BASE_DN = 'DC=corp,DC=doosan,DC=com'


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    try:
        server = Server(LDAP_SERVER, get_info=ALL)
        conn_ldap = Connection(server, user=f"DSG\\{username}", password=password, authentication=NTLM, auto_bind=True)

        if not conn_ldap.bind():
            raise Exception("Bind failed")

        conn_ldap.search(BASE_DN, f"(sAMAccountName={username})", attributes=['cn', 'mail'])
        if not conn_ldap.entries:
            raise Exception("LDAP user not found")

        ldap_user = conn_ldap.entries[0]
        email = ldap_user.mail.value
        full_name = ldap_user.cn.value

        # kontrola v databázi (povolení přístupu)
        cur.execute("SELECT * FROM users_ad WHERE email = %s", (email,))
        user = cur.fetchone()

        if not user:
            status_message = "You don´t have access to the application. Please contact the administrator."
            return templates.TemplateResponse("login.html", {"request": request,
                                                             "status_message": status_message})

        # aktualizace username pokud chybí
        if not user["username"]:
            cur.execute("UPDATE users_ad SET username = %s WHERE email = %s", (full_name, email))
            conn.commit()

        request.session["user_id"] = user["id"]
        request.session["username"] = full_name
        request.session["role"] = user["role"]
        request.session["id"] = user["id"]
        status_message = "Login successful"
        return templates.TemplateResponse("home.html", {"request": request, "status_message": status_message})

    except Exception as e:
        status_message = "Login failed: " + str(e)
        return templates.TemplateResponse("login.html", {"request": request,
                                                         "status_message": status_message})


@router.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
async def register_post(request: Request, email: str = Form(...)):
    try:
        msg = EmailMessage()
        msg['Subject'] = 'Nová žádost o přístup do aplikace'
        msg['From'] = 'webtest.mail@seznam.cz'
        msg['To'] = 'patrik.brejla@doosan.com'  # Změň na e-mail admina
        msg.set_content(f"Uživatel s e-mailem {email} žádá o přístup do aplikace.")

        with smtplib.SMTP_SSL("smtp.seznam.cz", 465) as smtp:
            smtp.login("webtest.mail@seznam.cz", "Webtest-123")
            smtp.send_message(msg)

        status_message = "Request sent to administrator."

    except Exception as e:
        status_message = "Failed to send email: " + str(e)

    return templates.TemplateResponse("login.html", {"request": request,
                                                     "status_message": status_message})


@router.get("/logout")
async def logout(request: Request):
    request.session.pop("user_id", None)
    request.session.pop("username", None)
    request.session.pop("role", None)
    request.session.pop("id", None)

    status_message = "Logout successful"
    return templates.TemplateResponse("login.html", {"request": request, "status_message": status_message})

