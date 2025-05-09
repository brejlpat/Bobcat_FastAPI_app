from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import configparser
from sqlalchemy import create_engine, text
import pandas as pd
import psycopg2
from psycopg2.extras import DictCursor
from app_state import state
from opcua import Client
import requests

router = APIRouter()

templates = Jinja2Templates(directory="templates")

"""
# Načtení konfiguračního souboru
config = configparser.ConfigParser()
config.read("config.ini")

db_config = config["database"]
MSserver = db_config["MSserver"]
MSdatabase = db_config["MSdatabase"]
MSusername = db_config["MSusername"]
MSpassword = db_config["MSpassword"]
MSdriver = db_config["MSdriver"]
MSconnection_string = f"mssql+pyodbc://{MSusername}:{MSpassword}@{MSserver}/{MSdatabase}?driver={MSdriver}"
"""

# Připojení k PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    dbname="postgres",
    user="postgres",
    password="postgres",
    port="5432"
)
cur = conn.cursor(cursor_factory=DictCursor)


def check_session(request: Request):
    return "user_id" in request.session


@router.get("/home", response_class=HTMLResponse)
async def home(request: Request):
    state.title = "Home Page"
    if "user_id" not in request.session:
        request.session["flash"] = {"message": "Please log in first!", "category": "error"}
        return RedirectResponse(url="/auth/login", status_code=302)
    try:
        if request.query_params.get("line"):
            line = request.query_params.get("line")
        else:
            line = request.session["line"]
    except Exception as e:
        line = "❌"
        request.session["line"] = line

    cur.execute("SELECT COUNT(*) FROM users_ad")
    users_amount = cur.fetchone()

    """
    try:
        MSengine = create_engine(MSconnection_string)
        MSconnection = MSengine.connect()
        #print("Successfully connected to MSSQL")
    except Exception as e:
        #print(f"Error: {e}")
        return templates.TemplateResponse("home.html", {
            "request": request,
            "title": "Domovská stránka",
            "data_list": [],
            "users_amount": users_amount,
            "is_connected": state.is_connected
        })

    query = text("SELECT TOP 10 * FROM dbo.HJ_Visual_plan3")
    result = MSconnection.execute(query)

    df = pd.DataFrame(result.fetchall(), columns=result.keys())
    df = df.fillna("N/A")
    data_list = df.to_dict(orient="records")
    """
    return templates.TemplateResponse("home.html", {
        "request": request,
        "title": state.title,
        #"data_list": data_list,
        "users_amount": users_amount,
        "is_connected": state.is_connected,
        "line": line
    })


@router.get("/plant_status", response_class=HTMLResponse)
async def plant_status(request: Request):
    if not check_session(request):
        return templates.TemplateResponse("login.html", {"request": request,
                                                         "status_message": "Please log in first!"})
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
        status_message = "✅ Connected"
    except Exception as e:
        status_message = f"❌ Connection error: {e}"
        state.is_connected = False

    root = opc_client.get_objects_node()
    channels = root.get_children()
    tags_with_values = []

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
                                    tag_name = tag.get_browse_name().Name
                                    tag_id = tag.nodeid.to_string()
                                    value = tag.get_value()
                                    tags_with_values.append({
                                        "name": tag_name,
                                        "nodeid": tag_id,
                                        "value": value
                                    })
                                except Exception as e:
                                    tags_with_values.append({
                                        "name": "❓",
                                        "nodeid": "❓",
                                        "value": f"⚠️ Error: {e}"
                                    })

    line = None
    state.is_connected = False
    request.session["line"] = line
    return templates.TemplateResponse("plant_status.html", {
        "request": request,
        "title": state.title,
        "tags": tags_with_values,
        "line": line,
        "is_connected": state.is_connected
    })


@router.get("/line_detail")
async def line_detail(request: Request):
    if not check_session(request):
        return templates.TemplateResponse("login.html", {"request": request,
                                                         "status_message": "Please log in first!"})
    state.title = "Line Detail"

    try:
        if request.query_params.get("line"):
            line = request.query_params.get("line")
        else:
            line = request.session["line"]
    except Exception as e:
        line = "❌"
        request.session["line"] = line

    return templates.TemplateResponse("plant_status_detail.html", {
        "request": request,
        "title": state.title,
        "line": line,
    })
