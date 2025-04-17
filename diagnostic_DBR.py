from opcua import Client, ua
from opcua.ua import uaerrors
import time

client = Client("opc.tcp://dbr-us-DFOPC.corp.doosan.com:49320")
client.set_security_string(
    "Basic256Sha256,SignAndEncrypt,"
    "certs_dbr/client_cert.der,"
    "certs_dbr/client_key.pem,"
    "certs_dbr/server_cert.der"
)

client.application_uri = "urn:FreeOpcUa:python:client"

client.set_user("DBR_Automation")
client.set_password("Kepserver_test1")

for ep in client.connect_and_get_server_endpoints():
    print("👉 SecurityPolicy:", ep.SecurityPolicyUri)
    for token in ep.UserIdentityTokens:
        print("   🔐 Token Type:", token.TokenType.name, "| Policy:", token.PolicyId)

try:
    print("🔌 Připojuji se k serveru...")
    client.connect()
    print("✅ Připojeno a aktivováno!")
except uaerrors.UaStatusCodeError as e:
    print(f"❌ UA Error: {e}")
except Exception as e:
    print(f"❌ Obecná chyba: {e}")

"""node = client.get_node("ns=2;s=PROD_DBR_TEST.Torque Tool.str3")
time.sleep(0.5)
val = ua.DataValue(ua.Variant("asdfjklů", ua.VariantType.String))
node.set_value(val)
print("✍️ Zapsáno!")"""

"""node = client.get_node("ns=2;s=PAINT_DBR_TEST.PLC_S7_TEST.int3")
val = ua.DataValue(ua.Variant(9999, ua.VariantType.UInt16))  # 12345 je příklad
node.set_value(val)
print("✍️ Zapsáno jako UInt16!")"""
