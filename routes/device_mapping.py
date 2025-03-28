from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from opcua import Client, ua

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Stav připojení
opc_client = None
is_connected = False
opc_value = None
status_message = "❌ Nepřipojeno"


@router.get("/lines", response_class=HTMLResponse)
async def devices(request: Request):
    return templates.TemplateResponse("device_mapping.html", {"request": request})


@router.get("/device", response_class=HTMLResponse)
async def device(request: Request):
    return templates.TemplateResponse("device.html", {
        "request": request,
        "is_connected": is_connected,
        "opc_value": opc_value,
        "status_message": status_message
    })


@router.post("/connect_opcua")
async def connect_opcua():
    global opc_client, is_connected, opc_value, status_message
    try:
        opc_client = Client("opc.tcp://127.0.0.1:49320")

        opc_client.connect()

        node = opc_client.get_node("ns=2;s=Channel2.Device1.str1")
        opc_value = node.get_value()
        is_connected = True
        status_message = "✅ Připojeno"
    except Exception as e:
        status_message = f"❌ Chyba připojení: {e}"
        is_connected = False
    return RedirectResponse(url="/device_mapping/device", status_code=303)


@router.post("/disconnect_opcua")
async def disconnect_opcua():
    global opc_client, is_connected, status_message
    if opc_client:
        opc_client.disconnect()
    opc_client = None
    is_connected = False
    status_message = "❌ Odpojeno"
    return RedirectResponse(url="/device_mapping/device", status_code=303)


def get_is_connected():
    return is_connected
