from opcua import Client
from opcua.ua.uaerrors import UaError

# 🧩 Změň si podle potřeby
OPC_URL = "opc.tcp://pct-kepdev.corp.doosan.com:49320"
USERNAME = "test"
PASSWORD = "Kepserver_test1"
CHANNEL_NAME = "Allen-Bradley-Ethernet"
DEVICE_NAME = "API_Peinture"
USE_SECURITY = True  # nastav True, pokud používáš certifikáty


def main():
    try:
        client = Client(OPC_URL)

        if USE_SECURITY:
            client.set_security_string(
                "Basic256Sha256,SignAndEncrypt,../certs/client_cert.der,../certs/client_key.pem,../certs/server_cert.der"
            )

        client.application_uri = "urn:FreeOpcUa:python:client"
        client.set_user("test")
        client.set_password("Kepserver_test1")
        client.connect()
        print("✅ Připojeno k OPC UA serveru\n")

        root = client.get_objects_node()
        channels = root.get_children()

        found_device = None

        for ch in channels:
            ch_name = ch.get_browse_name().Name
            if ch_name != CHANNEL_NAME:
                continue

            devices = ch.get_children()
            for dev in devices:
                dev_name = dev.get_browse_name().Name
                if dev_name == DEVICE_NAME:
                    found_device = dev
                    break

        if not found_device:
            print(f"❌ Zařízení '{DEVICE_NAME}' v kanálu '{CHANNEL_NAME}' nebylo nalezeno.")
            client.disconnect()
            return

        print(f"📡 Channel: {CHANNEL_NAME}")
        print(f"🖥️ Device: {DEVICE_NAME}")

        tags = found_device.get_children()
        for tag in tags:
            try:
                tag_name = tag.get_browse_name().Name
                tag_id = tag.nodeid.to_string()
                value = tag.get_value()
                print(f"  🔹 {tag_name} ({tag_id}) = {value}")
            except UaError as e:
                print(f"  ⚠️  Chyba u tagu: {e}")

        client.disconnect()
        print("\n🔌 Odpojeno od serveru")

    except Exception as e:
        print(f"❌ Výjimka: {e}")

if __name__ == "__main__":
    main()
