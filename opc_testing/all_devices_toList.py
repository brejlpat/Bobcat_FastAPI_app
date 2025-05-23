from opcua import Client
import os

# OPC UA připojení
opc_client = Client("opc.tcp://dbr-us-DFOPC.corp.doosan.com:49320")
opc_client.set_security_string(
    "Basic256Sha256,SignAndEncrypt,"
    "../certs_dbr/client_cert.der,"
    "../certs_dbr/client_key.pem,"
    "../certs_dbr/server_cert.der"
)

opc_client.application_uri = "urn:FreeOpcUa:python:client"
opc_client.set_user(os.getenv("kepserver_user"))
opc_client.set_password(os.getenv("kepserver_password"))
opc_client.connect()

print("✅ Připojeno k OPC UA")

objects = opc_client.get_objects_node()
channels = objects.get_children()

# Výstupní list channelů
channel_names = []

for ch in channels:
    ch_name = ch.get_browse_name().Name
    if ch_name.startswith("_") or ch_name == "Server":
        continue
    channel_names.append(ch_name)

opc_client.disconnect()
print("✅ Odpojeno")

# Výpis do terminálu
print("channel_names =", channel_names)

# Uložení do textového souboru
with open("channel_names.txt", "w", encoding="utf-8") as f:
    for name in channel_names:
        f.write(name + "\n")

print("📄 Uloženo do souboru channel_names.txt")
