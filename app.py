from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.routing import Route
from routes import routers
from routes.device_mapping import get_is_connected
from dotenv import load_dotenv
import os
import pprint

# Načtení proměnných z .env
# Load environment variables from .env file
load_dotenv()

# Vytvoření aplikace
# Create the FastAPI application
app = FastAPI()

# Přidání middleware pro session
# Add middleware for session management
app.add_middleware(SessionMiddleware, secret_key=os.getenv("APP_SECRET_KEY"))

# Načtení stylů a templates
# Load styles and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
templates.env.globals["is_connected"] = get_is_connected()

# Přidání routerů
# Add routers
for prefix, router in routers:
    app.include_router(router, prefix=f"/{prefix}", tags=[prefix])


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Zobrazí domovskou obrazovku.

    English:
    Displays the home screen.
    """
    return templates.TemplateResponse("login.html", {"request": request})
