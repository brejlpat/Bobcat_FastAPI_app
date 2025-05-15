from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
import pandas as pd
import psycopg2
from psycopg2.extras import DictCursor
from app_state import state
from opcua import Client
from routes.auth import get_current_user, User

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Připojení k PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    dbname="postgres",
    user="postgres",
    password="postgres",
    port="5432"
)
cur = conn.cursor(cursor_factory=DictCursor)


@router.get("/home", response_class=HTMLResponse)
async def home(request: Request, user: User = Depends(get_current_user)):
    state.title = "Home Page"
    line = request.query_params.get("line") or "❌"

    cur.execute("SELECT COUNT(*) FROM users_ad")
    users_amount = cur.fetchone()

    return templates.TemplateResponse("home.html", {
        "request": request,
        "title": state.title,
        "users_amount": users_amount,
        "is_connected": state.is_connected,
        "line": line,
        "username": user.username,
        "role": user.role
    })


@router.get("/plant_status", response_class=HTMLResponse)
async def plant_status(request: Request, user: User = Depends(get_current_user)):
    state.title = "Plant Status Overview"

    try:
        opc_client = Client("opc.tcp://dbr-us-DFOPC.corp.doosan.com:49320")
        opc_client.set_security_string(
            "Basic256Sha256,SignAndEncrypt,"
            "certs_dbr/client_cert.der,"
            "certs_dbr/client_key.pem,"
            "certs_dbr/server_cert.der"
        )

        opc_client.application_uri = "urn:FreeOpcUa:python:client"
        opc_client.set_user("DBR_Automation")
        opc_client.set_password("Kepserver_test1")
        opc_client.connect()

        state.is_connected = True
    except Exception as e:
        state.is_connected = False

    tags_with_values = []
    try:
        root = opc_client.get_objects_node()
        channels = root.get_children()
        for ch in channels:
            ch_name = ch.get_browse_name().Name
            if ch_name == "DBR_SITE_LINE_STATUS":
                devices = ch.get_children()
                for dev in devices:
                    dev_name = dev.get_browse_name().Name
                    if dev_name == "Line_Status":
                        for subfolder in dev.get_children():
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
        "is_connected": state.is_connected,
        "username": user.username,
        "role": user.role
    })


@router.get("/line_detail", response_class=HTMLResponse)
async def line_detail(request: Request, user: User = Depends(get_current_user)):
    state.title = "Line Detail"
    line = request.query_params.get("line") or "❌"

    return templates.TemplateResponse("plant_status_detail.html", {
        "request": request,
        "title": state.title,
        "line": line,
        "username": user.username,
        "role": user.role
    })
