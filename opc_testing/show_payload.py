import requests
from requests.auth import HTTPBasicAuth

channel = "Allen-Bradley-Ethernet"
device = "API_Peinture"

url = f"http://pct-kepdev.corp.doosan.com:57412/config/v1/project/channels/{channel}/devices/{device}"

response = requests.get(
    url,
    auth=HTTPBasicAuth("test", "Kepserver_test1"),
    headers={"Content-Type": "application/json"}
)

if response.status_code == 200:
    device_payload = response.json()
    print(device_payload)
else:
    print(f"Chyba {response.status_code}: {response.text}")
