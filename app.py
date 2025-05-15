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

load_dotenv()

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("APP_SECRET_KEY"))

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
templates.env.globals["is_connected"] = get_is_connected()

for prefix, router in routers:
    app.include_router(router, prefix=f"/{prefix}", tags=[prefix])


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


"""
@app.on_event("startup")
async def show_routes():
    print("📡 Registrované routy:")
    for route in app.routes:
        if isinstance(route, Route):
            print(f"{route.path} ({','.join(route.methods)})")
"""
