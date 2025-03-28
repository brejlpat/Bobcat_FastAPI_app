import requests
import json

# ✅ KEPServerEX REST API endpoint
url = "http://pct-kepdev.corp.doosan.com:57412/config/v1/project/channels"

# 🔐 Přihlášení
username = "test"
password = "Kepserver_test1"
headers = {"Content-Type": "application/json"}

# 🔧 Konfigurace nového kanálu
channel_name = "TESTING_DBR"

payload = {
    "common.ALLTYPES_NAME": channel_name,
    "common.ALLTYPES_DESCRIPTION": "",
    "servermain.MULTIPLE_TYPES_DEVICE_DRIVER": "OPC UA Client",
    "servermain.CHANNEL_DIAGNOSTICS_CAPTURE": False,
    "servermain.CHANNEL_WRITE_OPTIMIZATIONS_METHOD": 2,
    "servermain.CHANNEL_WRITE_OPTIMIZATIONS_DUTY_CYCLE": 10,
    "servermain.CHANNEL_NON_NORMALIZED_FLOATING_POINT_HANDLING": 1,
    "opcuaclient.CHANNEL_UA_SERVER_ENDPOINT_URL": "opc.tcp://10.52.32.214:4840",
    "opcuaclient.CHANNEL_UA_SERVER_SECURITY_POLICY": 0,
    "opcuaclient.CHANNEL_UA_SESSION_FAILED_CONNCTION_RETRY_INTERVAL_SECONDS": 5,
    "opcuaclient.CHANNEL_UA_SESSION_WATCHDOG_TIMEOUT": 5
    #"opcuaclient.CHANNEL_AUTHENTICATION_USERNAME": username,
    #"opcuaclient.CHANNEL_AUTHENTICATION_PASSWORD": password
}

# 📤 Odeslání požadavku
response = requests.post(url, headers=headers, data=json.dumps(payload), auth=(username, password))

# 📋 Výsledek
if response.status_code == 201:
    print(f"✅ Channel '{channel_name}' was successfully created!")
else:
    print(f"❌ Failed to create channel: {response.status_code}")
    print(response.text)
