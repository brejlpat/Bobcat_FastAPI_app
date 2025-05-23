from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.datastructures import FormData
from starlette.requests import Request
from opcua import Client, ua
from opcua.ua.uaerrors import UaError
import requests
from requests.auth import HTTPBasicAuth
import json
import shutil
from app_state import state
from routes.auth import get_current_user, User
import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import DictCursor

# Načtení .env souboru
# Load the .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# DB připojení
# DB connection
conn = psycopg2.connect(
    host="localhost",
    dbname="postgres",
    user=os.getenv("db_user"),
    password=os.getenv("db_password"),
    port="5432"
)
cur = conn.cursor(cursor_factory=DictCursor)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Stav připojení
# Connection state
opc_client = None
status_message = "❌ Disconnected"


@router.get("/lines", response_class=HTMLResponse)
async def devices(request: Request, user: User = Depends(get_current_user)):
    """
    Zobrazí obrazovku pro mapování zařízení.
    Uživatel si vybere linku a zobrazí se mu zařízení na této lince.

    English:
    Displays the device mapping screen.
    The user selects a line and the devices on that line are displayed.
    """

    await disconnect_opcua(request)
    state.title = "Device Mapping - Lines"

    return templates.TemplateResponse("device_mapping.html", {"request": request,
                                                              "is_connected": state.is_connected,
                                                              "title": state.title,
                                                              "username": user.username,
                                                              "role": user.role
                                                              })


@router.get("/device", response_class=HTMLResponse)
async def device(request: Request, user: User = Depends(get_current_user)):
    """
    Zobrazí obrazovku pro mapování zařízení na konkrétní lince.

    English:
    Displays the device mapping screen for a specific line.
    """

    global status_message
    line = request.query_params.get("line", "❌")
    state.line = line
    state.title = f"Device Mapping - {state.line}"
    return templates.TemplateResponse("device.html", {
        "request": request,
        "is_connected": state.is_connected,
        "status_message": status_message,
        "opc_devices": state.opc_devices,
        "line": state.line,
        "title": state.title,
        "username": user.username,
        "role": user.role
    })


@router.post("/connect_opcua")
async def connect_opcua(request: Request, user: User = Depends(get_current_user)):
    """
    Připojí se k OPC UA serveru a načte zařízení na vybrané lince.

    English:
    Connects to the OPC UA server and loads devices on the selected line.
    """

    global opc_client, status_message

    state.line = request.query_params.get("line", "❌")
    state.title = f"Device Mapping - {state.line}"
    try:
        opc_client = Client("opc.tcp://dbr-us-DFOPC.corp.doosan.com:49320")
        opc_client.set_security_string(
            "Basic256Sha256,SignAndEncrypt,"
            "certs_dbr/client_cert.der,"
            "certs_dbr/client_key.pem,"
            "certs_dbr/server_cert.der"
        )

        opc_client.application_uri = "urn:FreeOpcUa:python:client"
        opc_client.set_user(os.getenv("kepserver_user"))
        opc_client.set_password(os.getenv("kepserver_password"))
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
        if ch_name[0] != "_" and ch_name != "Server" and state.line in ch_name:
            for dev in ch.get_children():
                dev_name = dev.get_browse_name().Name
                if dev_name[0] != "_":
                    opc_devices.append({
                        "channel": ch_name,
                        "device": dev_name
                    })

    state.opc_devices = opc_devices

    return templates.TemplateResponse("device.html", {
        "request": request,
        "is_connected": state.is_connected,
        "status_message": status_message,
        "opc_devices": state.opc_devices,
        "title": state.title,
        "line": state.line,
        "username": user.username,
        "role": user.role
    })


@router.post("/disconnect_opcua")
async def disconnect_opcua(request: Request):
    """
    Odpojí se od OPC UA serveru.

    English:
    Disconnects from the OPC UA server.
    """

    global opc_client, status_message
    state.title = f"Device Mapping - Lines"
    if opc_client:
        opc_client.disconnect()
    opc_client = None
    state.is_connected = False
    status_message = "❌ Disconnected"
    return RedirectResponse(url="/device_mapping/lines", status_code=303)


@router.get("/channel_setting", response_class=HTMLResponse)
async def channel_setting(request: Request, user: User = Depends(get_current_user)):
    """
    Zobrazí obrazovku pro nastavení kanálu.
    Uživatel si vybere kanál a zobrazí se mu veškeré nastavení na tomto kanálu.

    English:
    Displays the screen for channel settings.
    The user selects a channel and all settings on that channel are displayed.
    """

    state.title = "Device Mapping - Driver Setting"
    line = request.query_params.get("line", "❌")
    state.line = line

    return templates.TemplateResponse("driver_setting.html", {"request": request, "is_connected": state.is_connected,
                                                              "title": state.title, "line": state.line,
                                                              "username": user.username,
                                                              "role": user.role})


def get_is_connected():
    """
    Funkce pro získání stavu připojení.

    English:
    Function to get the connection status.
    """

    return state.is_connected


@router.get("/device_details")
async def device_details(request: Request, user: User = Depends(get_current_user)):
    """
    Zobrazí podrobnosti o zařízení.
    Uživatel si může zobrazit všechny tagy pro zařízení.
    Uživatel může upravit zařízení & kanál.

    English:
    Displays device details.
    The user can view all tags for the device.
    The user can edit the device & channel.
    """

    channel = request.query_params.get("channel")
    device = request.query_params.get("device")
    line = request.query_params.get("line", "❌")
    state.line = line
    if not device:
        url_id = f"http://dbr-us-DFOPC.corp.doosan.com:57412/config/v1/project/channels/{channel}/devices"
        response = requests.get(url_id,
                                auth=HTTPBasicAuth(os.getenv("kepserver_user"), os.getenv("kepserver_password")),
                                headers={"Content-Type": "application/json"}
                                )
        device_data = response.json()
        if device_data:

            device_id = device_data[0].get("servermain.DEVICE_ID_STRING", "❌")  # IP address
            device = device_data[0].get("common.ALLTYPES_NAME", "❌")  # Device name

    state.title = f"{channel}"
    url_id = f"http://dbr-us-DFOPC.corp.doosan.com:57412/config/v1/project/channels/{channel}/devices/{device}"
    response = requests.get(url_id,
                            auth=HTTPBasicAuth(os.getenv("kepserver_user"), os.getenv("kepserver_password")),
                            headers={"Content-Type": "application/json"}
                            )
    device_data = response.json()
    if device_data:
        device_id = device_data.get("servermain.DEVICE_ID_STRING", "❌")     # IP address

    if "<" in device_id:
        device_id = device_id.split("<")[1]
        device_id = device_id.split(">")[0]

    device_info = {
        "channel": channel,
        "device": device,
        "device_id": device_id
    }
    state.is_connected = True
    status_message = "✅ Device details retrieved successfully."
    return templates.TemplateResponse("device_details.html", {"request": request,
                                                              "device_info": device_info,
                                                              "status_message": status_message,
                                                              "is_connected": state.is_connected,
                                                              "title": state.title,
                                                              "line": state.line,
                                                              "username": user.username,
                                                              "role": user.role
                                                              })


@router.get("/delete_device")
async def delete_device(request: Request, user: User = Depends(get_current_user)):
    """
    Smaže zařízení z kanálu.
    Je potřeba napsat Confirm do okna pro potvrzení smazání (JavaScript).

    English:
    Deletes the device from the channel.
    It is necessary to write Confirm in the confirmation window to confirm deletion.
    """
    channel = request.query_params.get("channel")
    device = request.query_params.get("device")

    state.title = f"Device Mapping - {state.line} devices"
    url_id = f"http://dbr-us-DFOPC.corp.doosan.com:57412/config/v1/project/channels/{channel}"

    get_response = requests.get(url_id, auth=HTTPBasicAuth(os.getenv("kepserver_user"), os.getenv("kepserver_password")),
                                headers={"Content-Type": "application/json"}
                                )
    if get_response.status_code == 200:
        try:
            channel_data = get_response.json()
            driver = channel_data.get("servermain.MULTIPLE_TYPES_DEVICE_DRIVER", "nothing1")
        except ValueError:
            driver = "nothing2"
    else:
        driver = "nothing3"

    response = requests.delete(url_id,
                               auth=HTTPBasicAuth(os.getenv("kepserver_user"), os.getenv("kepserver_password")),
                               headers={"Content-Type": "application/json"}
                               )

    try:
        delete_json = response.json()
    except ValueError:
        delete_json = {"info": f"Channel {channel} deleted"}

    image_path = f"static/images/DEVICES_MAP/{channel}.png"
    if os.path.exists(image_path):
        os.remove(image_path)

    if response.status_code == 200:
        status_message = "Device deleted successfully."
        cur.execute(
            "INSERT INTO device_edit (username, channel_name, payload, action, driver) VALUES (%s, %s, %s, %s, %s)",
            (user.username, channel, json.dumps(delete_json), "DELETE", driver)
        )
        conn.commit()
    else:
        status_message = "Failed to delete device."
    return templates.TemplateResponse("device.html", {"request": request, "status_message": status_message,
                                                      "is_connected": state.is_connected,
                                                      "title": state.title,
                                                      "line": state.line,
                                                      "username": user.username,
                                                      "role": user.role
                                                      })


@router.get("/show_tags", response_class=HTMLResponse)
async def show_tags(request: Request, user: User = Depends(get_current_user)):
    """
    Zobrazí tagy pro konkrétní zařízení.

    English:
    Displays tags for a specific device.
    """

    channel = request.query_params.get("channel")
    device = request.query_params.get("device")
    device_id = request.query_params.get("device_id")
    line = request.query_params.get("line", "❌")
    state.line = line

    opc_url = "opc.tcp://dbr-us-DFOPC.corp.doosan.com:49320"
    username = "DBR_Automation"
    password = "Kepserver_test1"
    use_security = True

    tags_with_values = []

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
        "line": state.line,
        "username": user.username,
        "role": user.role
    })


@router.get("/cancel_tags")
async def cancel_tags(request: Request, user: User = Depends(get_current_user)):
    """
    Zavře tagy pro konkrétní zařízení.

    English:
    Closes tags for a specific device.
    """

    channel = request.query_params.get("channel")
    device = request.query_params.get("device")
    device_id = request.query_params.get("device_id")

    tags_with_values = []
    status_message = "Tags closed."

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
        "is_connected": state.is_connected,
        "username": user.username,
        "role": user.role
    })


@router.get("/edit_device", response_class=HTMLResponse)
async def edit_device_get(request: Request, user: User = Depends(get_current_user)):
    """
    Zobrazí obrazovku pro úpravu zařízení.
    Uživatel si vybere zařízení a zobrazí se mu veškeré nastavení na tomto zařízení.

    English:
    Displays the screen for editing the device.
    The user selects a device and all settings on that device are displayed.
    """

    global device_payload
    channel = request.query_params.get("channel")
    device = request.query_params.get("device")
    device_id = request.query_params.get("device_id")

    url = f"http://dbr-us-DFOPC.corp.doosan.com:57412/config/v1/project/channels/{channel}/devices/{device}"
    response = requests.get(
        url,
        auth=HTTPBasicAuth(os.getenv("kepserver_user"), os.getenv("kepserver_password")),
        headers={"Content-Type": "application/json"}
    )

    device_payload = response.json()
    project_id = device_payload.get("PROJECT_ID", "❌")
    if not device_payload:
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
        "is_connected": state.is_connected,
        "username": user.username,
        "role": user.role
    })


@router.post("/edit_device")
async def edit_device_post(request: Request, user: User = Depends(get_current_user)):
    """
    Endpoint pro úpravu zařízení.
    Všechny změny z formuláře se porovnají s payloadem a přidají se do payloadu.
    Poté se odešle PATCH požadavek na úpravu zařízení.

    English:
    Endpoint for editing the device.
    All changes from the form are compared with the payload and added to the payload.
    Then a PATCH request is sent to edit the device.
    """

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

    for key, original_value in device_payload.items():
        # Získáš hodnotu z formuláře jen pokud tam opravdu existuje
        if key in form:
            form_value = str(form[key])
            original_value = str(original_value)
            if form_value != original_value:
                payload[key] = form_value

    log_payload = payload.copy()
    log_payload.pop("PROJECT_ID", None)

    # Endpoint pro úpravu channelu
    url = f"http://dbr-us-DFOPC.corp.doosan.com:57412/config/v1/project/channels/{channel}/devices/{device}"

    # Přihlašovací údaje
    username = os.getenv("kepserver_user")
    password = os.getenv("kepserver_password")
    headers = {"Content-Type": "application/json"}

    get_response = requests.get(url_id,
                                auth=HTTPBasicAuth(os.getenv("kepserver_user"), os.getenv("kepserver_password")),
                                headers={"Content-Type": "application/json"}
                                )
    if get_response.status_code == 200:
        try:
            channel_data = get_response.json()
            driver = channel_data.get("servermain.MULTIPLE_TYPES_DEVICE_DRIVER", "nothing1")
        except ValueError:
            driver = "nothing2"
    else:
        driver = "nothing3"

    # Odeslání požadavku na úpravu (PATCH = částečná změna)
    response = requests.put(url, headers=headers, data=json.dumps(payload), auth=(username, password))

    # Výstup
    if response.status_code == 200:
        status_message = f"✅ Device was successfully edited!\nTo see the changes you need to disconnect and connect again."
        cur.execute(
            "INSERT INTO device_edit (username, channel_name, payload, action, driver) VALUES (%s, %s, %s, %s, %s)",
            (user.username, channel, json.dumps(log_payload), "EDIT", driver)
        )
        conn.commit()
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
        "is_connected": state.is_connected,
        "username": user.username,
        "role": user.role
    })


@router.get("/edit_channel", response_class=HTMLResponse)
async def edit_channel_get(request: Request, user: User = Depends(get_current_user)):
    """
        Zobrazí obrazovku pro úpravu kanálu.
        Uživatel si vybere kanál a zobrazí se mu veškeré nastavení.

        English:
        Displays the screen for editing the channel.
        The user selects a channel and all settings on that channel are displayed.
        """
    global channel_payload
    channel = request.query_params.get("channel")
    device = request.query_params.get("device")
    device_id = request.query_params.get("device_id")

    url = f"http://dbr-us-DFOPC.corp.doosan.com:57412/config/v1/project/channels/{channel}"
    response = requests.get(
        url,
        auth=HTTPBasicAuth(os.getenv("kepserver_user"), os.getenv("kepserver_password")),
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
        "is_connected": state.is_connected,
        "username": user.username,
        "role": user.role
    })


@router.post("/edit_channel")
async def edit_channel_post(request: Request, user: User = Depends(get_current_user)):
    """
        Endpoint pro úpravu kanálu.
        Všechny změny z formuláře se porovnají s payloadem a přidají se do payloadu.
        Poté se odešle PATCH požadavek na úpravu kanálu.

        English:
        Endpoint for editing the channel.
        All changes from the form are compared with the payload and added to the payload.
        Then a PATCH request is sent to edit the channel.
    """
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

    # Odeslání PATCH požadavku
    url = f"http://dbr-us-DFOPC.corp.doosan.com:57412/config/v1/project/channels/{channel}"
    response = requests.put(
        url,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        auth=HTTPBasicAuth(os.getenv("kepserver_user"), os.getenv("kepserver_password"))
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
        "is_connected": state.is_connected,
        "username": user.username,
        "role": user.role
    })
