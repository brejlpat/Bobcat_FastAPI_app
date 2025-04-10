from opcua import Client
import requests
from requests.auth import HTTPBasicAuth

# OPC UA připojení
opc_client = Client("opc.tcp://pct-kepdev.corp.doosan.com:49320")
opc_client.set_security_string(
    "Basic256Sha256,SignAndEncrypt,"
    "../certs/client_cert.der,"
    "../certs/client_key.pem,"
    "../certs/server_cert.der"
)

opc_client.application_uri = "urn:FreeOpcUa:python:client"
opc_client.set_user("test")
opc_client.set_password("Kepserver_test1")
opc_client.connect()

print("✅ Připojeno k OPC UA")

objects = opc_client.get_objects_node()
channels = objects.get_children()

# REST API přihlašovací údaje
base_url = "http://pct-kepdev.corp.doosan.com:57412"
auth = HTTPBasicAuth("test", "Kepserver_test1")
headers = {"Content-Type": "application/json"}

# Načti zařízení z REST API
for ch in channels:
    ch_name = ch.get_browse_name().Name
    if ch_name.startswith("_") or ch_name == "Server":
        continue

    url = f"{base_url}/config/v1/project/channels/{ch_name}/devices"
    response = requests.get(url, auth=auth, headers=headers)

    if response.status_code != 200:
        print(f"❌ Chyba při načítání zařízení z kanálu '{ch_name}': {response.status_code}")
        continue

    devices_data = response.json()

    for d in devices_data:
        device_name = d.get("common.ALLTYPES_NAME", "❓")
        device_id = d.get("servermain.DEVICE_ID_STRING", "❌")
        print(f"[{ch_name}] Zařízení: {device_name} → IP: {device_id}")

opc_client.disconnect()
print("✅ Odpojeno")
