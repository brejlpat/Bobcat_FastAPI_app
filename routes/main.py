from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import configparser
from sqlalchemy import create_engine, text
import pandas as pd
import psycopg2
from psycopg2.extras import DictCursor
from app_state import state

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


@router.get("/home", response_class=HTMLResponse)
async def home(request: Request):
    if "user_id" not in request.session:
        request.session["flash"] = {"message": "Please log in first!", "category": "error"}
        return RedirectResponse(url="/auth/login", status_code=302)

    cur.execute("SELECT COUNT(*) FROM users")
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
        "is_connected": state.is_connected
    })
