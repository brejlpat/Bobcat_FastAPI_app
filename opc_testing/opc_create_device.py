import requests
import json

# Konfigurace
channel_name = "test_cloos2"
device_name = "MyNewDevice10"
url = f"http://127.0.0.1:57412/config/v1/project/channels/{channel_name}/devices"

# Přihlašovací údaje pro REST API Kepware
username = "test"
password = "Kepserver_test1"
headers = {"Content-Type": "application/json"}

# JSON konfigurace pro OPC UA klienta s nastavením bezpečnosti
payload = {
    "common.ALLTYPES_NAME": device_name,
    "common.ALLTYPES_DESCRIPTION": "",
    "servermain.MULTIPLE_TYPES_DEVICE_DRIVER": "OPC UA Client",
    "servermain.CHANNEL_DIAGNOSTICS_CAPTURE": False,
    "servermain.CHANNEL_STATIC_TAG_COUNT": 0,
    "servermain.CHANNEL_WRITE_OPTIMIZATIONS_METHOD": 2,
    "servermain.CHANNEL_WRITE_OPTIMIZATIONS_DUTY_CYCLE": 10,
    "servermain.CHANNEL_NON_NORMALIZED_FLOATING_POINT_HANDLING": 1,

    # Nastavení OPC UA endpointu
    "opcuaclient.CHANNEL_UA_SERVER_ENDPOINT_URL": "opc.tcp://10.52.32.214:4840",

    # Bezpečnostní politika: 3 = Basic256Sha256
    "opcuaclient.CHANNEL_UA_SERVER_SECURITY_POLICY": 3,
    # Režim zabezpečení zpráv: 3 = SignAndEncrypt
    "opcuaclient.CHANNEL_UA_SERVER_MESSAGE_MODE": 3,

    # Časové limity
    "opcuaclient.CHANNEL_UA_SESSION_CONNECT_TIMEOUT_SECONDS": 30,
    "opcuaclient.CHANNEL_UA_SESSION_TIMEOUT_INACTIVE_MINUTES": 20,
    "opcuaclient.CHANNEL_UA_SESSION_RENEWAL_INTERVAL_MINUTES": 60,
    "opcuaclient.CHANNEL_UA_SESSION_FAILED_CONNCTION_RETRY_INTERVAL_SECONDS": 5,
    "opcuaclient.CHANNEL_UA_SESSION_WATCHDOG_TIMEOUT": 5,

    # Přihlášení k OPC UA serveru (pokud je vyžadováno)
    "opcuaclient.CHANNEL_AUTHENTICATION_USERNAME": username,
    "opcuaclient.CHANNEL_AUTHENTICATION_PASSWORD": password
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
    print(f"✅ Zařízení '{device_name}' bylo úspěšně vytvořeno v kanálu '{channel_name}'!")
else:
    print(f"❌ Chyba při vytváření zařízení: {response.status_code}")
    print(response.text)
