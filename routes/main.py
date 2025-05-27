from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
import psycopg2
from psycopg2.extras import DictCursor
from app_state import state
from opcua import Client
from routes.auth import get_current_user, User
import os
from pathlib import Path
from dotenv import load_dotenv

# Načtení .env souboru
# Load the .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Připojení k PostgreSQL
# Connection to PostgreSQL
conn = psycopg2.connect(
    host=os.getenv("db_host"),
    dbname="postgres",
    user=os.getenv("db_user"),
    password=os.getenv("db_password"),
    port="5432"
)
cur = conn.cursor(cursor_factory=DictCursor)


@router.get("/home", response_class=HTMLResponse)
async def home(request: Request, user: User = Depends(get_current_user)):
    """
    Zobrazí domovskou obrazovku.

    English:
    Displays the home screen.
    """
    state.title = "Home Page"
    line = request.query_params.get("line") or "❌"

    return templates.TemplateResponse("home.html", {
        "request": request,
        "title": state.title,
        "line": line,
        "username": user.username,
        "role": user.role
    })


@router.get("/plant_status", response_class=HTMLResponse)
async def plant_status(request: Request, user: User = Depends(get_current_user)):
    """
    Zobrazí plán závodu a stav linek.

    English:
    Displays the plant layout and line status.
    """
    state.title = "Plant Status Overview"

    # Zde se připojujeme k OPC UA serveru a získáváme hodnoty tagů
    # Here we connect to the OPC UA server and retrieve tag values
    try:
        opc_client = Client("opc.tcp://dbr-us-DFOPC.corp.doosan.com:49320")
        opc_client.set_security_string(
            "Basic256Sha256,SignAndEncrypt,"
            "certs_dbr/client_cert.der,"
            "certs_dbr/client_key.pem,"
            "certs_dbr/server_cert.der"
        )

        opc_client.application_uri = "urn:FreeOpcUa:python:client"
        opc_client.set_user(os.getenv("kepserver_user"))
        opc_client.set_password(os.getenv("kepserver_password"))
        opc_client.connect()
        status_message = "✅ Successfully connected to OPC UA server."
    except Exception as e:
        status_message = f"⚠️ Error connecting to OPC UA server: {e}"

    tags_with_values = []
    try:
        root = opc_client.get_objects_node()
        channels = root.get_children()
        for ch in channels:
            ch_name = ch.get_browse_name().Name
            # Potřebujeme channel DBR_SITE_LINE_STATUS
            # We need channel DBR_SITE_LINE_STATUS
            if ch_name == "DBR_SITE_LINE_STATUS":
                devices = ch.get_children()
                for dev in devices:
                    dev_name = dev.get_browse_name().Name
                    if dev_name == "Line_Status":
                        for subfolder in dev.get_children():
                            # Zde procházíme jednotlivé tagy a vybíráme jenom line_status + ukládáme do listu tags_with_values
                            # Here we browse through individual tags and select only line_status + save to list tags_with_values
                            if subfolder.get_browse_name().Name == "line_status":
                                line_status_tags = subfolder.get_variables()
                                for tag in line_status_tags:
                                    try:
                                        tags_with_values.append({
                                            "name": tag.get_browse_name().Name,
                                            "nodeid": tag.nodeid.to_string(),
                                            "value": tag.get_value()
                                        })
                                    except Exception as e:
                                        tags_with_values.append({
                                            "name": "❓",
                                            "nodeid": "❓",
                                            "value": f"⚠️ Error: {e}"
                                        })
    except:
        pass

    line = request.query_params.get("line") or "❌"

    return templates.TemplateResponse("plant_status.html", {
        "request": request,
        "title": state.title,
        "tags": tags_with_values,
        "line": line,
        "status_message": status_message,
        "username": user.username,
        "role": user.role
    })


@router.get("/line_detail", response_class=HTMLResponse)
async def line_detail(request: Request, user: User = Depends(get_current_user)):
    """
    Zobrazí detailní pohled na linku.
    Uživatel má možnost procházet jednotlivé zařízení a jejich hodnoty.

    English:
    Displays a detailed view of the line.
    The user can browse through individual devices and their values.
    """
    state.title = "Line Detail"
    line = request.query_params.get("line") or "❌"

    return templates.TemplateResponse("plant_status_detail.html", {
        "request": request,
        "title": state.title,
        "line": line,
        "username": user.username,
        "role": user.role
    })
