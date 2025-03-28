from opcua import Client, ua
import time

# Ověř správný port a endpoint
server_url = "opc.tcp://127.0.0.1:49320"

# Nastav zabezpečení (zkus None pro test)
client = Client(server_url)
#client.set_security_string("Basic256Sha256")
print("🔐 Connecting to KEPServerEX OPC UA...")
client.connect()
print("✅ Connected KEPServerEX OPC UA!")

node = client.get_node("ns=2;s=Channel2.Device1.str1")
print(node.get_value())
time.sleep(0.5)
val = ua.DataValue(ua.Variant("test", ua.VariantType.String))
node.set_value(val)
time.sleep(0.5)
print(node.get_value())
