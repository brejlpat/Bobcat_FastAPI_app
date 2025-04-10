from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from opcua import Client, ua
import requests
from requests.auth import HTTPBasicAuth
import os

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Stav připojení
opc_client = None
is_connected = False
status_message = "❌ Disconnected"


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
        status_message = "✅ Connected"
    except Exception as e:
        status_message = f"❌ Connection error: {e}"
        is_connected = False

    opc_devices = []
    objects = opc_client.get_objects_node()
    channels = objects.get_children()

    for ch in channels:
        ch_name = ch.get_browse_name().Name
        if ch_name[0] != "_" and ch_name != "Server":
            for dev in ch.get_children():
                dev_name = dev.get_browse_name().Name
                if dev_name[0] != "_":
                    opc_devices.append({
                        "channel": ch_name,
                        "device": dev_name
                    })

    request.session["opc_devices"] = opc_devices
    request.session["is_connected"] = is_connected
    request.session["status_message"] = status_message
    return templates.TemplateResponse("device.html", {
        "request": request,
        "is_connected": is_connected,
        "status_message": status_message,
        "opc_devices": opc_devices
    })


@router.post("/disconnect_opcua")
async def disconnect_opcua():
    global opc_client, is_connected, status_message
    if opc_client:
        opc_client.disconnect()
    opc_client = None
    is_connected = False
    status_message = "❌ Disconnected"
    return RedirectResponse(url="/device_mapping/device", status_code=303)


@router.get("/channel_setting", response_class=HTMLResponse)
async def channel_setting(request: Request):
    return templates.TemplateResponse("driver_setting.html", {"request": request})


def get_is_connected():
    return is_connected


@router.get("/device_details")
async def device_details(request: Request):
    channel = request.query_params.get("channel")
    device = request.query_params.get("device")
    url_id = f"http://pct-kepdev.corp.doosan.com:57412/config/v1/project/channels/{channel}/devices/{device}"
    response = requests.get(url_id,
                            auth=HTTPBasicAuth("test", "Kepserver_test1"),
                            headers={"Content-Type": "application/json"}
                            )
    device_data = response.json()
    if device_data:
        device_id = device_data.get("servermain.DEVICE_ID_STRING", "❌")
    device_info = {
        "channel": channel,
        "device": device,
        "device_id": device_id
    }
    status_message = "✅ Device details retrieved successfully."
    return templates.TemplateResponse("device_details.html", {"request": request, "device_info": device_info, "status_message": status_message})


@router.get("/delete_device")
async def delete_device(request: Request):
    channel = request.query_params.get("channel")
    device = request.query_params.get("device")
    url_id = f"http://pct-kepdev.corp.doosan.com:57412/config/v1/project/channels/{channel}"
    response = requests.delete(url_id,
                               auth=HTTPBasicAuth("test", "Kepserver_test1"),
                               headers={"Content-Type": "application/json"}
                               )

    image_path = f"static/images/{device}.png"
    if os.path.exists(image_path):
        os.remove(image_path)

    if response.status_code == 200:
        status_message = "Device deleted successfully."
    else:
        status_message = "Failed to delete device."
    return templates.TemplateResponse("device.html", {"request": request, "status_message": status_message})


@router.get("/show_tags")
async def show_tags(request: Request):
    global opc_client
    channel = request.query_params.get("channel")
    device = request.query_params.get("device")
    device_id = request.query_params.get("device_id")

    # Získání tagů přes REST API
    url_id = f"http://pct-kepdev.corp.doosan.com:57412/config/v1/project/channels/{channel}/devices/{device}/tags"
    response = requests.get(
        url_id,
        auth=HTTPBasicAuth("test", "Kepserver_test1"),
        headers={"Content-Type": "application/json"}
    )

    tags_with_values = []

    if response.status_code == 200:
        tags_data = response.json()

        for tag in tags_data:
            tag_name = tag.get("common.ALLTYPES_NAME", "❓")
            tag_address = tag.get("servermain.TAG_ADDRESS")
            tag_value = "❌"

            if tag_address and opc_client:
                node = opc_client.get_node(tag_address)
                tag_value = node.get_value()

            tags_with_values.append({
                "name": tag_name,
                "value": tag_value
            })
        print(tags_with_values)

        status_message = "✅ Tags loaded successfully."
    else:
        status_message = f"❌ Error when loading tags: {response.status_code}"

    device_info = {
        "channel": channel,
        "device": device,
        "device_id": device_id
    }

    return templates.TemplateResponse("device_details.html", {
        "request": request,
        "tags": tags_with_values,
        "status_message": status_message,
        "device_info": device_info
    })


@router.get("/cancel_tags")
async def cancel_tags(request: Request):
    channel = request.query_params.get("channel")
    device = request.query_params.get("device")
    device_id = request.query_params.get("device_id")

    tags_with_values = []
    status_message = "Tags cleared."

    device_info = {
        "channel": channel,
        "device": device,
        "device_id": device_id
    }

    return templates.TemplateResponse("device_details.html", {
        "request": request,
        "tags": tags_with_values,
        "status_message": status_message,
        "device_info": device_info
    })
