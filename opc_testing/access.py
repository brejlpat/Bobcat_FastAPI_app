import requests
from requests.auth import HTTPBasicAuth

base_url = "http://pct-kepdev.corp.doosan.com:57412/config/v1/project"
auth = HTTPBasicAuth("test", "Kepserver_test1")
headers = {"Content-Type": "application/json"}

# 1️⃣ Získej kanály
channels_url = f"{base_url}/channels"
channels_response = requests.get(channels_url, auth=auth, headers=headers)

if channels_response.status_code == 200:
    channels = channels_response.json()

    for ch in channels:
        ch_name = ch["common.ALLTYPES_NAME"]

        # 2️⃣ Získej zařízení v kanálu
        devices_url = f"{base_url}/channels/{ch_name}/devices"
        devices_response = requests.get(devices_url, auth=auth, headers=headers)

        if devices_response.status_code == 200:
            devices = devices_response.json()

            for dev in devices:
                dev_name = dev["common.ALLTYPES_NAME"]

                # 3️⃣ Získej detail zařízení
                device_detail_url = f"{base_url}/channels/{ch_name}/devices/{dev_name}"
                detail_response = requests.get(device_detail_url, auth=auth, headers=headers)

                if detail_response.status_code == 200:
                    data = detail_response.json()
                    device_id = data.get("servermain.DEVICE_ID_STRING", "❌")
                    print(f"{ch_name} / {dev_name} → IP: {device_id}")
