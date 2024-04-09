import paho.mqtt.client as paho

# Callback function for message received
def on_message(client, userdata, msg):
    print(f"Received message: {msg.topic} - {msg.payload.decode()}")

# Set up the MQTT client
client = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION2)

# Set the username and password for authentication
client.username_pw_set("abenstirling", "ruXnkMdhU9@FkM")

# Enable TLS for secure connection
client.tls_set(tls_version=paho.ssl.PROTOCOL_TLS)

# Set the callback function for message received
client.on_message = on_message

# Connect to the HiveMQ broker
client.connect("85b1e9de27974ad59481eff128ffc12d.s1.eu.hivemq.cloud", 8883)

# Subscribe to the topics
client.subscribe("client1/data", qos=1)
client.subscribe("client2/data", qos=1)

# Start the MQTT client loop
client.loop_forever()