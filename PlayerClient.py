# import os
# import json
# from dotenv import load_dotenv

# import paho.mqtt.client as paho
# from paho import mqtt
# import time


# # setting callbacks for different events to see if it works, print the message etc.
# def on_connect(client, userdata, flags, rc, properties=None):
#     """
#         Prints the result of the connection with a reasoncode to stdout ( used as callback for connect )
#         :param client: the client itself
#         :param userdata: userdata is set when initiating the client, here it is userdata=None
#         :param flags: these are response flags sent by the broker
#         :param rc: stands for reasonCode, which is a code for the connection result
#         :param properties: can be used in MQTTv5, but is optional
#     """
#     print("CONNACK received with code %s." % rc)


# # with this callback you can see if your publish was successful
# def on_publish(client, userdata, mid, properties=None):
#     """
#         Prints mid to stdout to reassure a successful publish ( used as callback for publish )
#         :param client: the client itself
#         :param userdata: userdata is set when initiating the client, here it is userdata=None
#         :param mid: variable returned from the corresponding publish() call, to allow outgoing messages to be tracked
#         :param properties: can be used in MQTTv5, but is optional
#     """
#     print("mid: " + str(mid))


# # print which topic was subscribed to
# def on_subscribe(client, userdata, mid, granted_qos, properties=None):
#     """
#         Prints a reassurance for successfully subscribing
#         :param client: the client itself
#         :param userdata: userdata is set when initiating the client, here it is userdata=None
#         :param mid: variable returned from the corresponding publish() call, to allow outgoing messages to be tracked
#         :param granted_qos: this is the qos that you declare when subscribing, use the same one for publishing
#         :param properties: can be used in MQTTv5, but is optional
#     """
#     print("Subscribed: " + str(mid) + " " + str(granted_qos))


# # print message, useful for checking if it was successful
# def on_message(client, userdata, msg):
#     """
#         Prints a mqtt message to stdout ( used as callback for subscribe )
#         :param client: the client itself
#         :param userdata: userdata is set when initiating the client, here it is userdata=None
#         :param msg: the message with topic and payload
#     """

#     print("message: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))


# if __name__ == '__main__':
#     load_dotenv(dotenv_path='./credentials.env')
    
#     broker_address = os.environ.get('BROKER_ADDRESS')
#     broker_port = int(os.environ.get('BROKER_PORT'))
#     username = os.environ.get('USER_NAME')
#     password = os.environ.get('PASSWORD')

#     client = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION1, client_id="Player1", userdata=None, protocol=paho.MQTTv5)
    
#     # enable TLS for secure connection
#     client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
#     # set username and password
#     client.username_pw_set(username, password)
#     # connect to HiveMQ Cloud on port 8883 (default for MQTT)
#     client.connect(broker_address, broker_port)
#     print("PlayerClient connected to broker")

#     # setting callbacks, use separate functions like above for better visibility
#     client.on_subscribe = on_subscribe # Can comment out to not print when subscribing to new topics
#     client.on_message = on_message
#     client.on_publish = on_publish # Can comment out to not print when publishing to topics

#     print("Got here now")
#     lobby_name = "rip"
#     player_name1 = "Player1"
#     player_name2 = "Player2"
#     player_name3 = "Player3"
    
#     client.subscribe(f"games/{lobby_name}/lobby")
#     client.subscribe(f"games/{lobby_name}/+/game_state")
#     client.subscribe(f"games/{lobby_name}/scores")

#     client.publish("new_game", json.dumps({'lobby_name':lobby_name,
#                                             'team_name':'ATeam',
#                                             'player_name' : player_name1}))
#     client.publish("new_game", json.dumps({'lobby_name':lobby_name,
#                                             'team_name':'TeamB',
#                                             'player_name' : player_name2}))
#     client.publish("new_game", json.dumps({'lobby_name':lobby_name,
#                                             'team_name':'TeamB',
#                                             'player_name' : player_name3}))
    
#     print("Got here now")   
#     # delay to allow for subscription
#     time.sleep(.5)
#     #starting
#     client.publish(f"games/{lobby_name}/start", "START")
#     client.publish(f"games/{lobby_name}/{player_name1}/move", "UP")
#     client.publish(f"games/{lobby_name}/{player_name2}/move", "UP")
#     client.publish(f"games/{lobby_name}/{player_name3}/move", "DOWN")
    
#     #cooldown time
#     time.sleep(.5)
#     #stopping
#     client.publish(f"games/{lobby_name}/start", "STOP")
#     client.loop_forever()
import os
import json
import random
import threading
from dotenv import load_dotenv
import paho.mqtt.client as paho
from paho import mqtt
import time

def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)

def on_publish(client, userdata, mid, properties=None):
    print("mid: " + str(mid))

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_message(client, userdata, msg):
    print("message: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

if __name__ == '__main__':
    load_dotenv(dotenv_path='./credentials.env')
    
    broker_address = os.environ.get('BROKER_ADDRESS')
    broker_port = int(os.environ.get('BROKER_PORT'))
    username = os.environ.get('USER_NAME') 
    password = os.environ.get('PASSWORD')

    clients = []
    for i in range(1, 5):
        client = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION1, client_id=f"Player{i}", userdata=None, protocol=paho.MQTTv5)
        client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
        client.username_pw_set(username, password)
        client.connect(broker_address, broker_port)
        print(f"Player{i} connected to broker")
        
        client.on_subscribe = on_subscribe
        client.on_message = on_message 
        client.on_publish = on_publish
        clients.append(client)

    lobby_name = "Lobby1"
    team1 = "Team1"
    team2 = "Team2"

    for i, client in enumerate(clients):
        time.sleep(3)
        team = team1 if i < 2 else team2
        player_name = f"Player{i+1}"
        
        client.subscribe(f"games/{lobby_name}/lobby")
        client.subscribe(f"games/{lobby_name}/{player_name}/game_state")
        client.subscribe(f"games/{lobby_name}/scores")
        
        new_player = {
            'lobby_name': lobby_name,
            'team_name': team,
            'player_name': player_name
        }
        client.publish("new_game", json.dumps(new_player))
        time.sleep(3)
        thread = threading.Thread(target=client.loop_forever)
        thread.start()

    time.sleep(3)
    clients[0].publish(f"games/{lobby_name}/start", "START")

    while True:
        for client in clients:
            player_name = client._client_id.decode()  # Decode player name from byte string
            
            # Make a random move
            moves = ["RIGHT", "LEFT", "UP", "DOWN"]
            move = random.choice(moves)
            client.publish(f"games/{lobby_name}/{player_name}/move", move)
        
        time.sleep(3) 