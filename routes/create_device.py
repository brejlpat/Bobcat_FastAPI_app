from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
import requests
import json

router = APIRouter()

templates = Jinja2Templates(directory="templates")


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
    status_message = "testing"
    # 📤 Odeslání požadavku
    """response = requests.post(url, headers=headers, data=json.dumps(payload), auth=(username, password))

    if response.status_code == 201:
        status_message = f"Channel '{channel_name}' was successfully created!"
    else:
        status_message = f"Failed to create channel: {response.status_code}"""

    return templates.TemplateResponse("device_setting.html", {
        "request": request,
        "status_message": status_message
    })

