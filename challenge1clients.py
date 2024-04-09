import time
import random
import paho.mqtt.client as paho

# Set up the MQTT client
client1 = paho.Client(client_id="client1", callback_api_version=paho.CallbackAPIVersion.VERSION2)
client2 = paho.Client(client_id="client2", callback_api_version=paho.CallbackAPIVersion.VERSION2)

# Set the username and password for authentication
client1.username_pw_set("abenstirling", "ruXnkMdhU9@FkM")
client2.username_pw_set("abenstirling", "ruXnkMdhU9@FkM")

# Enable TLS for secure connection
client1.tls_set(tls_version=paho.ssl.PROTOCOL_TLS)
client2.tls_set(tls_version=paho.ssl.PROTOCOL_TLS)

# Connect to the HiveMQ broker
client1.connect("85b1e9de27974ad59481eff128ffc12d.s1.eu.hivemq.cloud", 8883)
client2.connect("85b1e9de27974ad59481eff128ffc12d.s1.eu.hivemq.cloud", 8883)

# Publish random data every 3 seconds
while True:
    # Generate random data
    data1 = random.randint(0, 100)
    data2 = random.randint(0, 100)

    # Publish the data to unique topics
    client1.publish("client1/data", payload=str(data1), qos=1)
    client2.publish("client2/data", payload=str(data2), qos=1)

    # Wait for 3 seconds before publishing the next data
    time.sleep(3)