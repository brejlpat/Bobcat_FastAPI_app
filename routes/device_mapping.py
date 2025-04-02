from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from opcua import Client, ua

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Stav připojení
opc_client = None
is_connected = False
status_message = "❌ Nepřipojeno"


@router.get("/lines", response_class=HTMLResponse)
async def devices(request: Request):
    return templates.TemplateResponse("device_mapping.html", {"request": request})


@router.get("/device", response_class=HTMLResponse)
async def device(request: Request):
    global is_connected, status_message
    opc_devices = request.session.get("opc_devices", [])
    return templates.TemplateResponse("device.html", {
        "request": request,
        "is_connected": is_connected,
        "status_message": status_message,
        "opc_devices": opc_devices
    })


@router.post("/connect_opcua")
async def connect_opcua(request: Request):
    global opc_client, is_connected, status_message
    try:
        opc_client = Client("opc.tcp://pct-kepdev.corp.doosan.com:49320")
        opc_client.set_security_string(
            "Basic256Sha256,SignAndEncrypt,"
            "certs/client_cert.der,"
            "certs/client_key.pem,"
            "certs/server_cert.der"
        )

        opc_client.application_uri = "urn:FreeOpcUa:python:client"
        opc_client.set_user("test")
        opc_client.set_password("Kepserver_test1")
        opc_client.connect()

        is_connected = True
        status_message = "✅ Připojeno"
    except Exception as e:
        status_message = f"❌ Chyba připojení: {e}"
        is_connected = False

    opc_devices = []
    objects = opc_client.get_objects_node()
    channels = objects.get_children()

    for ch in channels:
        ch_name = ch.get_browse_name().Name
        if ch_name in ["PAINT_DBR_TEST", "PROD_DBR_TEST"]:
            for dev in ch.get_children():
                dev_name = dev.get_browse_name().Name
                if dev_name[0] != "_":
                    tags_list = []
                    for tag in dev.get_children():
                        tag_name = tag.get_browse_name().Name
                        if tag_name[0] != "_":
                            try:
                                tag_value = tag.get_value()
                            except:
                                tag_value = "❌"
                            tags_list.append({
                                "name": tag_name,
                                "value": tag_value
                            })
                    opc_devices.append({
                        "channel": ch_name,
                        "device": dev_name,
                        "tags": tags_list
                    })

    request.session["opc_devices"] = opc_devices
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


@router.get("/channel_setting", response_class=HTMLResponse)
async def channel_setting(request: Request):
    return templates.TemplateResponse("driver_setting.html", {"request": request})
