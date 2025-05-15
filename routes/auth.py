from fastapi import APIRouter, Request, Form, status, Depends, HTTPException, Cookie
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from pydantic import BaseModel
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.templating import Jinja2Templates
from ldap3 import Server, Connection, ALL, NTLM
from email.message import EmailMessage
import smtplib
import psycopg2
from psycopg2.extras import DictCursor
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

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

# JWT konfigurace
SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 125

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    username: str
    role: str


class TokenData(BaseModel):
    username: str
    role: str


def authenticate_ldap_user(username: str, password: str):
    try:
        server = Server(LDAP_SERVER, get_info=None)
        conn_ldap = Connection(server, user=f"DSG\\{username}", password=password, authentication=NTLM, auto_bind=True)
        if not conn_ldap.bind():
            return None

        conn_ldap.search(BASE_DN, f"(sAMAccountName={username})", attributes=["cn", "mail"])
        if not conn_ldap.entries:
            return None

        user = conn_ldap.entries[0]
        return {"email": user.mail.value, "username": user.cn.value}
    except Exception:
        return None


def get_user_from_db(email: str):
    cur.execute("SELECT * FROM users_ad WHERE email = %s", (email,))
    return cur.fetchone()


def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Vytvoří JWT token, který expiruje po `expires_delta` (nebo 5 minut defaultně).
    Používá správný Unix timestamp v klíči `exp`.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=120) + timedelta(minutes=30)
    exp_timestamp = int(expire.timestamp())

    to_encode.update({"exp": exp_timestamp})

    print(f"📦 JWT payload: {to_encode} (vyprší v {expire.isoformat()} UTC)")
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(access_token: str = Cookie(None)) -> User:
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated (no cookie)")

    try:
        token = access_token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        print("📦 JWT payload:", payload)

        username: str = payload.get("username")
        role: str = payload.get("role")

        if username is None or role is None:
            raise HTTPException(status_code=401, detail="Invalid token content")

        return User(username=username, role=role)
    except ExpiredSignatureError:
        print("❌ Token expired")
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError as e:
        print("❌ JWT decode error:", e)
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    ldap_user = authenticate_ldap_user(username, password)
    if not ldap_user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "status_message": "Invalid LDAP credentials"
        })

    db_user = get_user_from_db(ldap_user["email"])
    if not db_user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "status_message": "User not authorized in application"
        })

    # Aktualizace username pokud chybí
    if not db_user["username"]:
        cur.execute("UPDATE users_ad SET username = %s WHERE email = %s",
                    (ldap_user["username"], ldap_user["email"]))
        conn.commit()

    access_token = create_access_token(
        data={"username": ldap_user["username"], "role": db_user["role"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES+120)
    )

    print(f"Nový token: {access_token}\nExpires in {ACCESS_TOKEN_EXPIRE_MINUTES}")

    response = templates.TemplateResponse("home.html", {
        "request": request,
        "username": ldap_user["username"],
        "role": db_user["role"],
        "status_message": "Login successful ✅"
    })
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # True pokud nasadíš na HTTPS
        samesite="lax"
    )

    return response


@router.post("/token", response_model=Token)
async def login_token(form_data: OAuth2PasswordRequestForm = Depends()):
    ldap_user = authenticate_ldap_user(form_data.username, form_data.password)
    if not ldap_user:
        raise HTTPException(status_code=401, detail="Invalid credentials (LDAP)")

    db_user = get_user_from_db(ldap_user["email"])
    if not db_user:
        raise HTTPException(status_code=403, detail="Access denied – not in app DB")

    if not db_user["username"]:
        cur.execute("UPDATE users_ad SET username = %s WHERE email = %s",
                    (ldap_user["username"], ldap_user["email"]))
        conn.commit()

    access_token = create_access_token(data={"username": ldap_user["username"], "role": db_user["role"]})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
async def get_my_profile(user: TokenData = Depends(get_current_user)):
    return {
        "username": user.username,
        "role": user.role,
    }


@router.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
async def register_post(request: Request, email: str = Form(...)):
    try:
        msg = EmailMessage()
        msg['Subject'] = 'New Access Request – Doosan Bobcat Web Application'
        msg['From'] = 'webtest.mail@seznam.cz'
        msg['To'] = 'patrik.brejla@doosan.com' # admin email
        msg.set_content(
            f"""Hello,
        
        A user with the email address {email} has submitted a request to access the internal Doosan Bobcat web application.
        
        Please review and approve the request in the account management section.
        
        Best regards,  
        Bobcat Automation Team"""
        )

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
    status_message = "Logout successful ✅"
    return templates.TemplateResponse("login.html", {"request": request, "status_message": status_message})

