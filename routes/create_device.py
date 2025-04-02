from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
import requests
import json

router = APIRouter()

templates = Jinja2Templates(directory="templates")


@router.post("/channel")
async def channel(
        request: Request,
        driver: str = Form(...)
):
    return templates.TemplateResponse("channel_setting.html", {"request": request, "driver": driver})


@router.post("/create_channel")
async def create_channel(
        request: Request,
        channel_name: str = Form(...),
        driver: str = Form(...),
        endpoint_url: str = Form(...),
        description: str = Form("")
):
    # KEPServerEX REST API endpoint
    url = "http://pct-kepdev.corp.doosan.com:57412/config/v1/project/channels"

    # Přihlášení
    username = "test"
    password = "Kepserver_test1"
    headers = {"Content-Type": "application/json"}

    payload = {
        "common.ALLTYPES_NAME": channel_name,
        "common.ALLTYPES_DESCRIPTION": description,
        "servermain.MULTIPLE_TYPES_DEVICE_DRIVER": driver,
        "servermain.CHANNEL_DIAGNOSTICS_CAPTURE": False,
        "servermain.CHANNEL_WRITE_OPTIMIZATIONS_METHOD": 2,
        "servermain.CHANNEL_WRITE_OPTIMIZATIONS_DUTY_CYCLE": 10,
        "servermain.CHANNEL_NON_NORMALIZED_FLOATING_POINT_HANDLING": 1,
        "opcuaclient.CHANNEL_UA_SERVER_ENDPOINT_URL": endpoint_url,
        "opcuaclient.CHANNEL_UA_SERVER_SECURITY_POLICY": 0,
        "opcuaclient.CHANNEL_UA_SESSION_FAILED_CONNCTION_RETRY_INTERVAL_SECONDS": 5,
        "opcuaclient.CHANNEL_UA_SESSION_WATCHDOG_TIMEOUT": 5
    }

    # 📤 Odeslání požadavku
    response = requests.post(url, headers=headers, data=json.dumps(payload), auth=(username, password))

    if response.status_code == 201:
        status_message = f"Channel '{channel_name}' was successfully created!"
    else:
        status_message = f"Failed to create channel: {response.status_code}"

    return templates.TemplateResponse("device_setting.html", {
        "request": request,
        "status_message": status_message,
        "channel_name": channel_name,
        "driver": driver
    })


@router.post("/create_OPC_UA_CLIENT_device")
async def create_OPC_UA_CLIENT_device(
        request: Request,
        device_name: str = Form(...),
        channel_name: str = Form(...),
        driver: str = Form(...),
        description: str = Form(...)
):
    url = f"http://pct-kepdev.corp.doosan.com:57412/config/v1/project/channels/{channel_name}/devices"

    # Přihlašovací údaje pro REST API Kepware
    username = "test"
    password = "Kepserver_test1"
    headers = {"Content-Type": "application/json"}

    # JSON konfigurace pro OPC UA klienta s nastavením bezpečnosti
    payload = {
        "common.ALLTYPES_NAME": device_name,
        "common.ALLTYPES_DESCRIPTION": description,
        "servermain.MULTIPLE_TYPES_DEVICE_DRIVER": driver,
        "servermain.DEVICE_MODEL": 0,
        "servermain.DEVICE_CHANNEL_ASSIGNMENT": channel_name,
        "servermain.DEVICE_DATA_COLLECTION": True,
        "servermain.DEVICE_SIMULATED": False,
        "servermain.DEVICE_STATIC_TAG_COUNT": 0,
        "servermain.DEVICE_SCAN_MODE": 0,
        "servermain.DEVICE_SCAN_MODE_RATE_MS": 1000,
        "servermain.DEVICE_SCAN_MODE_PROVIDE_INITIAL_UPDATES_FROM_CACHE": False,
        "opcuaclient.DEVICE_SUBSCRIPTION_PUBLISHING_INTERVAL_MILLISECONDS": 1000,
        "opcuaclient.DEVICE_SUBSCRIPTION_MAX_NOTIFICATIONS_PER_PUBLISH": 0,
        "opcuaclient.DEVICE_SUBSCRIPTION_UPDATE_MODE": 0,
        "opcuaclient.DEVICE_SUBSCRIPTION_REGISTERED_READWRITE": True,
        "opcuaclient.DEVICE_MAX_ITEMS_PER_READ": 512,
        "opcuaclient.DEVICE_MAX_ITEMS_PER_WRITE": 512,
        "opcuaclient.DEVICE_READ_TIMEOUT_MS": 1000,
        "opcuaclient.DEVICE_WRITE_TIMEOUT_MS": 1000,
        "opcuaclient.DEVICE_READ_AFTER_WRITE": True,
        "opcuaclient.DEVICE_INITIAL_TIMEOUT_MS": 5000,
        "opcuaclient.DEVICE_CONNECTION_LIFETIME_COUNT": 60,
        "opcuaclient.DEVICE_CONNECTION_MAX_KEEP_ALIVE": 5,
        "opcuaclient.DEVICE_CONNECTION_PRIORITY": 0,
        "opcuaclient.DEVICE_MONITORED_ITEMS_SAMPLE_INTERVAL_MILLISECONDS": 500,
        "opcuaclient.DEVICE_MONITORED_ITEMS_QUEUE_SIZE": 1,
        "opcuaclient.DEVICE_MONITORED_ITEMS_DISCARD_OLDEST": True,
        "opcuaclient.DEVICE_MONITORED_ITEMS_DEADBAND_TYPE": 0,
        "opcuaclient.DEVICE_MONITORED_ITEMS_DEADBAND_VALUE": 0,
        "redundancy.DEVICE_SECONDARY_PATH": "",
        "redundancy.DEVICE_OPERATING_MODE": 0,
        "redundancy.DEVICE_MONITOR_ITEM": "",
        "redundancy.DEVICE_MONITOR_ITEM_POLL_INTERVAL": 300,
        "redundancy.DEVICE_FAVOR_PRIMARY": True,
        "redundancy.DEVICE_TRIGGER_ITEM": "",
        "redundancy.DEVICE_TRIGGER_ITEM_SCAN_RATE": 1000,
        "redundancy.DEVICE_TRIGGER_TYPE": 0,
        "redundancy.DEVICE_TRIGGER_OPERATOR": 0,
        "redundancy.DEVICE_TRIGGER_VALUE": "",
        "redundancy.DEVICE_TRIGGER_TIMEOUT": 10000
    }

    # Odeslání požadavku na REST API Kepware
    response = requests.post(
        url,
        headers=headers,
        data=json.dumps(payload),
        auth=(username, password)
    )

    # Výsledek
    if response.status_code == 201:
        status_message = f"✅ Zařízení '{device_name}' bylo úspěšně vytvořeno v kanálu '{channel_name}'!"
    else:
        status_message = f"❌ Chyba při vytváření zařízení: {response.status_code}"

    return templates.TemplateResponse("tag_setting.html", {"request": request,
                                                           "status_message": status_message,
                                                           "device_name": device_name,
                                                           "channel_name": channel_name})


@router.post("/create_tag")
async def create_tag(
        request: Request,
        channel_name: str = Form(...),
        device_name: str = Form(...),
        tag_name: str = Form(...),
        tag_data_type: int = Form(...),
        description: str = Form(...)
):
    url = f"http://pct-kepdev.corp.doosan.com:57412/config/v1/project/channels/{channel_name}/devices/{device_name}/tags"

    # Přihlašovací údaje pro REST API Kepware
    username = "test"
    password = "Kepserver_test1"
    headers = {"Content-Type": "application/json"}

    # JSON konfigurace pro OPC UA klienta s nastavením bezpečnosti
    payload = {
        "common.ALLTYPES_NAME": tag_name,
        "common.ALLTYPES_DESCRIPTION": description,
        "servermain.TAG_ADDRESS": f"ns=3;s={channel_name}.{device_name}.{tag_name}",
        "servermain.TAG_DATA_TYPE": int(tag_data_type),
        "servermain.TAG_READ_WRITE_ACCESS": 1,
        "servermain.TAG_SCAN_RATE_MILLISECONDS": 100,
        "servermain.TAG_AUTOGENERATED": False,
        "servermain.TAG_SCALING_TYPE": 0,
        "servermain.TAG_SCALING_RAW_LOW": 0,
        "servermain.TAG_SCALING_RAW_HIGH": 1000,
        "servermain.TAG_SCALING_SCALED_DATA_TYPE": 9,
        "servermain.TAG_SCALING_SCALED_LOW": 0,
        "servermain.TAG_SCALING_SCALED_HIGH": 1000,
        "servermain.TAG_SCALING_CLAMP_LOW": False,
        "servermain.TAG_SCALING_CLAMP_HIGH": False,
        "servermain.TAG_SCALING_NEGATE_VALUE": False,
        "servermain.TAG_SCALING_UNITS": ""
    }

    # Odeslání požadavku na REST API Kepware
    response = requests.post(
        url,
        headers=headers,
        data=json.dumps(payload),
        auth=(username, password)
    )

    print("Request payload:", json.dumps(payload, indent=2))
    print("Response:", response.status_code)
    print("Response text:", response.text)

    # Výsledek
    if response.status_code == 201:
        status_message = f"✅ Zařízení '{device_name}' bylo úspěšně vytvořeno v kanálu '{channel_name}'!"
    else:
        status_message = f"❌ Chyba při vytváření zařízení: {response.status_code}"

    return templates.TemplateResponse("device.html", {"request": request, "status_message": status_message})
