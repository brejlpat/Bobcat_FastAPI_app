from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app_state import state

router = APIRouter()

templates = Jinja2Templates(directory="templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    team_members = [
        {"name": "Cyrille Piteau", "position": "Automation & Digitalisation senior manager EMEA", "image": "user_icon.png"},
        {"name": "Bořek Miklas", "position": "ME Engineer - Smart Factory", "image": "user_icon.png"},
        {"name": "Sivakumar Siva", "position": "Automation Control Engineer", "image": "user_icon.png"},
        {"name": "Zdeněk Křížek", "position": "Technologist", "image": "user_icon.png"},
        {"name": "Patrik Brejla", "position": "Trainee Automation", "image": "user_icon.png"},
    ]
    return templates.TemplateResponse("automation.html", {"request": request, "team_members": team_members,
                                                          "is_connected": state.is_connected})
