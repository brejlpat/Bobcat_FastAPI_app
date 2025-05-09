from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app_state import state

router = APIRouter()

templates = Jinja2Templates(directory="templates")


def check_session(request: Request):
    return "user_id" in request.session


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    if not check_session(request):
        return templates.TemplateResponse("login.html", {"request": request,
                                                         "status_message": "Please log in first!"})
    if request.query_params.get("line"):
        line = request.query_params.get("line")
        request.session["line"] = line  # <-- tady se to musí uložit
    else:
        line = request.session.get("line", "❌")

    team_members = [
        {"name": "Cyrille Piteau", "position": "Automation & Digitalisation senior manager EMEA", "image": "user_icon.png"},
        {"name": "Bořek Miklas", "position": "ME Engineer - Smart Factory", "image": "user_icon.png"},
        {"name": "Sivakumar Siva", "position": "Automation Control Engineer", "image": "user_icon.png"},
        {"name": "Zdeněk Křížek", "position": "Technologist", "image": "user_icon.png"},
        {"name": "Patrik Brejla", "position": "Trainee Automation", "image": "user_icon.png"},
    ]
    return templates.TemplateResponse("automation.html", {"request": request, "team_members": team_members,
                                                          "is_connected": state.is_connected, "line": line})
