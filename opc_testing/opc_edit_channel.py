import requests
import json

# Název channelu, který chceš upravit
channel_name = "TEST1"

# Endpoint pro úpravu channelu
url = f"http://pct-kepdev.corp.doosan.com:57412/config/v1/project/channels/{channel_name}"

# Přihlašovací údaje
username = "test"
password = "Kepserver_test1"
headers = {"Content-Type": "application/json"}

# Parametry, které chceš upravit
payload = {
    "PROJECT_ID": 849594037,
    "common.ALLTYPES_DESCRIPTION": "Updated description for TEST1"
}

# Odeslání požadavku na úpravu (PATCH = částečná změna)
response = requests.put(url, headers=headers, data=json.dumps(payload), auth=(username, password))

# Výstup
if response.status_code == 200:
    print("✅ Channel byl úspěšně upraven!")
else:
    print(f"❌ Chyba při úpravě channelu: {response.status_code}")
    print(response.text)
