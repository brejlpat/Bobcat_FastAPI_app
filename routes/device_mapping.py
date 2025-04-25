from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.datastructures import FormData
from starlette.requests import Request
from opcua import Client, ua
from opcua.ua.uaerrors import UaError
import requests
from requests.auth import HTTPBasicAuth
import os
import json
import shutil
from app_state import state

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Stav připojení
opc_client = None
status_message = "❌ Disconnected"


@router.get("/lines", response_class=HTMLResponse)
async def devices(request: Request):
    await disconnect_opcua()
    state.title = "Device Mapping - Lines"

    return templates.TemplateResponse("device_mapping.html", {"request": request,
                                                              "is_connected": state.is_connected,
                                                              "title": state.title
                                                              })


@router.get("/device", response_class=HTMLResponse)
async def device(request: Request):
    global status_message
    if request.query_params.get("line"):
        line = request.query_params.get("line")
        request.session["line"] = line  # <-- tady se to musí uložit
    else:
        line = request.session.get("line", "❌")

    opc_devices = request.session.get("opc_devices", [])
    state.title = f"Device Mapping - {line}"
    return templates.TemplateResponse("device.html", {
        "request": request,
        "is_connected": state.is_connected,
        "status_message": status_message,
        "opc_devices": opc_devices,
        "line": line,
        "title": state.title
    })


@router.post("/connect_opcua")
async def connect_opcua(request: Request):
    global opc_client, status_message
    if request.query_params.get("line"):
        line = request.query_params.get("line")
        request.session["line"] = line  # <-- tady se to musí uložit
    else:
        line = request.session.get("line", "❌")

    state.title = f"Device Mapping - {line}"
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

    opc_devices = []
    objects = opc_client.get_objects_node()
    channels = objects.get_children()

    for ch in channels:
        ch_name = ch.get_browse_name().Name
        if ch_name[0] != "_" and ch_name != "Server" and line in ch_name:
            for dev in ch.get_children():
                dev_name = dev.get_browse_name().Name
                if dev_name[0] != "_":
                    opc_devices.append({
                        "channel": ch_name,
                        "device": dev_name
                    })

    request.session["opc_devices"] = opc_devices
    request.session["is_connected"] = state.is_connected
    request.session["status_message"] = status_message
    return templates.TemplateResponse("device.html", {
        "request": request,
        "is_connected": state.is_connected,
        "status_message": status_message,
        "opc_devices": opc_devices,
        "title": state.title,
        "line": line
    })


@router.post("/disconnect_opcua")
async def disconnect_opcua():
    global opc_client, status_message
    state.title = f"Device Mapping - Lines"
    if opc_client:
        opc_client.disconnect()
    opc_client = None
    state.is_connected = False
    status_message = "❌ Disconnected"
    return RedirectResponse(url="/device_mapping/lines", status_code=303)


@router.get("/channel_setting", response_class=HTMLResponse)
async def channel_setting(request: Request):
    state.title = "Device Mapping - Driver Setting"
    if request.query_params.get("line"):
        line = request.query_params.get("line")
        request.session["line"] = line  # <-- tady se to musí uložit
    else:
        line = request.session.get("line", "❌")

    return templates.TemplateResponse("driver_setting.html", {"request": request, "is_connected": state.is_connected,
                                                              "title": state.title, "line": line})


def get_is_connected():
    return state.is_connected


@router.get("/device_details")
async def device_details(request: Request):
    channel = request.query_params.get("channel")
    device = request.query_params.get("device")
    if request.query_params.get("line"):
        line = request.query_params.get("line")
        request.session["line"] = line  # <-- tady se to musí uložit
    else:
        line = request.session.get("line", "❌")

    state.title = f"{channel}"
    url_id = f"http://dbr-us-DFOPC.corp.doosan.com:57412/config/v1/project/channels/{channel}/devices/{device}"
    response = requests.get(url_id,
                            auth=HTTPBasicAuth("DBR_Automation", "Kepserver_test1"),
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
    return templates.TemplateResponse("device_details.html", {"request": request,
                                                              "device_info": device_info,
                                                              "status_message": status_message,
                                                              "is_connected": state.is_connected,
                                                              "title": state.title,
                                                              "line": line})


@router.get("/delete_device")
async def delete_device(request: Request):
    channel = request.query_params.get("channel")
    device = request.query_params.get("device")

    state.title = f"Device Mapping - {request.session.get('line')} devices"
    url_id = f"http://dbr-us-DFOPC.corp.doosan.com:57412/config/v1/project/channels/{channel}"
    response = requests.delete(url_id,
                               auth=HTTPBasicAuth("DBR_Automation", "Kepserver_test1"),
                               headers={"Content-Type": "application/json"}
                               )

    image_path = f"static/images/DEVICES/{channel}.png"
    if os.path.exists(image_path):
        os.remove(image_path)

    if response.status_code == 200:
        status_message = "Device deleted successfully."
    else:
        status_message = "Failed to delete device."
    return templates.TemplateResponse("device.html", {"request": request, "status_message": status_message,
                                                      "is_connected": state.is_connected,
                                                      "title": state.title,
                                                      "line": request.session["line"]
                                                      })


@router.get("/show_tags", response_class=HTMLResponse)
async def show_tags(request: Request):
    channel = request.query_params.get("channel")
    device = request.query_params.get("device")
    device_id = request.query_params.get("device_id")
    if request.query_params.get("line"):
        line = request.query_params.get("line")
        request.session["line"] = line
    else:
        line = request.session.get("line", "❌")

    opc_url = "opc.tcp://dbr-us-DFOPC.corp.doosan.com:49320"
    username = "DBR_Automation"
    password = "Kepserver_test1"
    use_security = True

    tags_with_values = []
    status_message = ""

    try:
        opc_client = Client(opc_url)

        if use_security:
            opc_client.set_security_string(
                "Basic256Sha256,SignAndEncrypt,certs_dbr/client_cert.der,certs_dbr/client_key.pem,certs_dbr/server_cert.der"
            )

        opc_client.application_uri = "urn:FreeOpcUa:python:client"
        opc_client.set_user(username)
        opc_client.set_password(password)
        opc_client.connect()

        root = opc_client.get_objects_node()
        channels = root.get_children()

        found_device = None

        for ch in channels:
            ch_name = ch.get_browse_name().Name
            if ch_name != channel:
                continue

            devices = ch.get_children()
            for dev in devices:
                dev_name = dev.get_browse_name().Name
                if dev_name == device:
                    found_device = dev
                    break

        if not found_device:
            status_message = f"❌ Device '{device}' in channel '{channel}' not found."
        else:
            tags = found_device.get_variables()
            for tag in tags:
                try:
                    tag_name = tag.get_browse_name().Name
                    tag_id = tag.nodeid.to_string()
                    value = tag.get_value()
                    tags_with_values.append({
                        "name": tag_name,
                        "nodeid": tag_id,
                        "value": value
                    })
                except UaError as e:
                    tags_with_values.append({
                        "name": "❓",
                        "nodeid": "❓",
                        "value": f"⚠️ Error: {e}"
                    })

            status_message = "✅ OPC UA tags successfully loaded."

        opc_client.disconnect()

    except Exception as e:
        status_message = f"❌ Exception: {e}"

    device_info = {
        "channel": channel,
        "device": device,
        "device_id": device_id
    }

    return templates.TemplateResponse("device_details.html", {
        "request": request,
        "tags": tags_with_values,
        "device_info": device_info,
        "status_message": status_message,
        "is_connected": state.is_connected,
        "line": line
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
        "device_info": device_info,
        "is_connected": state.is_connected
    })


@router.get("/edit_device", response_class=HTMLResponse)
async def edit_device_get(request: Request):
    global device_payload
    channel = request.query_params.get("channel")
    device = request.query_params.get("device")
    device_id = request.query_params.get("device_id")

    url = f"http://dbr-us-DFOPC.corp.doosan.com:57412/config/v1/project/channels/{channel}/devices/{device}"
    response = requests.get(
        url,
        auth=HTTPBasicAuth("DBR_Automation", "Kepserver_test1"),
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        device_payload = response.json()
        project_id = device_payload.get("PROJECT_ID", "❌")
    else:
        device_payload = {}

    device_info = {
        "channel": channel,
        "device": device,
        "device_id": device_id
    }

    return templates.TemplateResponse("edit_device.html", {
        "request": request,
        "device_info": device_info,
        "payload": device_payload,
        "project_id": project_id,
        "is_connected": state.is_connected
    })


@router.post("/edit_device")
async def edit_device_post(request: Request):
    global device_payload
    form = await request.form()

    channel = request.query_params.get("channel")
    device = request.query_params.get("device")
    device_id = request.query_params.get("device_id")
    project_id = request.query_params.get("project_id")

    payload = {
        "PROJECT_ID": int(project_id),
    }

    new_name = str(form["common.ALLTYPES_NAME"])
    old_name = str(device_payload["common.ALLTYPES_NAME"])
    #print(f"NEW_name: {new_name} ---------- OLD_name: {old_name}")

    for key, form_value, payload_value in zip(device_payload.keys(), form.values(), device_payload.values()):
        form_value_string = str(form_value)
        payload_value_string = str(payload_value)
        if form_value_string != payload_value_string:
            payload[key] = form_value

    # Endpoint pro úpravu channelu
    url = f"http://dbr-us-DFOPC.corp.doosan.com:57412/config/v1/project/channels/{channel}/devices/{device}"

    # Přihlašovací údaje
    username = "DBR_Automation"
    password = "Kepserver_test1"
    headers = {"Content-Type": "application/json"}

    # Odeslání požadavku na úpravu (PATCH = částečná změna)
    response = requests.put(url, headers=headers, data=json.dumps(payload), auth=(username, password))

    # Výstup
    if response.status_code == 200:
        status_message = f"✅ Device was successfully edited!\nTo see the changes you need to disconnect and connect again."
    else:
        status_message = f"❌ Error while editing the device: {response.status_code}"

    device_info = {
        "channel": channel,
        "device": new_name,
        "device_id": device_id
    }

    return templates.TemplateResponse("device_details.html", {
        "request": request,
        "device_info": device_info,
        "status_message": status_message,
        "is_connected": state.is_connected
    })


@router.get("/edit_channel", response_class=HTMLResponse)
async def edit_channel_get(request: Request):
    global channel_payload
    channel = request.query_params.get("channel")
    device = request.query_params.get("device")
    device_id = request.query_params.get("device_id")

    url = f"http://dbr-us-DFOPC.corp.doosan.com:57412/config/v1/project/channels/{channel}"
    response = requests.get(
        url,
        auth=HTTPBasicAuth("DBR_Automation", "Kepserver_test1"),
        headers={"Content-Type": "application/json"}
    )

    project_id = "❌"
    if response.status_code == 200:
        channel_payload = response.json()
        project_id = channel_payload.get("PROJECT_ID", "❌")
    else:
        channel_payload = {}

    device_info = {
        "channel": channel,
        "device": device,
        "device_id": device_id
    }

    return templates.TemplateResponse("edit_channel.html", {
        "request": request,
        "device_info": device_info,
        "payload": channel_payload,
        "project_id": project_id,
        "is_connected": state.is_connected
    })


@router.post("/edit_channel")
async def edit_channel_post(request: Request):
    global channel_payload
    form = await request.form()

    channel = request.query_params.get("channel")
    device = request.query_params.get("device")
    device_id = request.query_params.get("device_id")
    project_id = request.query_params.get("project_id")

    payload = {
        "PROJECT_ID": int(project_id)
    }

    new_name = str(form["common.ALLTYPES_NAME"])
    old_name = str(channel_payload.get("common.ALLTYPES_NAME", ""))

    # Přejmenování obrázku, pokud se změnil název
    if new_name != old_name:
        old_image_path = f"static/images/DEVICES/{old_name}.png"
        new_dir = f"static/images/DEVICES"
        new_image_path = os.path.join(new_dir, f"{new_name}.png")

        if os.path.exists(old_image_path):
            os.makedirs(new_dir, exist_ok=True)
            shutil.move(old_image_path, new_image_path)
            #print(f"✅ Obrázek přejmenován na: {new_image_path}")

    # Porovnej hodnoty z formuláře s payloadem a přidej změněné klíče
    for key, form_value in form.items():
        if key in channel_payload:
            form_str = str(form_value)
            orig_str = str(channel_payload[key])
            if form_str != orig_str:
                payload[key] = form_value

    #print("📦 Payload k odeslání:")
    #print(json.dumps(payload, indent=2))

    # Odeslání PATCH požadavku
    url = f"http://dbr-us-DFOPC.corp.doosan.com:57412/config/v1/project/channels/{channel}"
    response = requests.put(
        url,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        auth=HTTPBasicAuth("DBR_Automation", "Kepserver_test1")
    )

    if response.status_code == 200:
        status_message = "✅ Channel edited successfully!\nTo see the changes you need to disconnect and connect again."
    else:
        status_message = f"❌ Error occured: {response.status_code}\n{response.text}"

    device_info = {
        "channel": new_name,
        "device": device,
        "device_id": device_id
    }

    return templates.TemplateResponse("device_details.html", {
        "request": request,
        "device_info": device_info,
        "status_message": status_message,
        "is_connected": state.is_connected
    })
