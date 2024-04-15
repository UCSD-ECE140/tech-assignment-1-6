import os
import json
from dotenv import load_dotenv

import paho.mqtt.client as paho
from paho import mqtt
import time
import random
from collections import deque

# Dictionary to store the global map for each team
team_maps = {}
player_team_dict = {}
prev_player_positions = {}
player_move_history = {}

state_mapping = {'unexplored': '·', 'free': ' ', 'wall': '#', 'coin': '⬤', 'player': 'P'}

def create_empty_map():
    # Create an initial empty map filled with unknown values
    return [[state_mapping['unexplored']] * 10 for _ in range(10)]

# object can be 'free', 'wall', 'coin', 'player'
def update_team_map(team_name: str, coords: list, object: str):
    team_maps[team_name][coords[0]][coords[1]] = state_mapping[object]

def print_map(map_2d):
    """
    Print a 2D list as a grid.
    :param map_2d: 2D list representing the team map
    """
    print("Current Map:")
    for row in map_2d:
        print(" ".join(str(item) for item in row))
        
# setting callbacks for different events to see if it works, print the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
    """
        Prints the result of the connection with a reasoncode to stdout ( used as callback for connect )
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param flags: these are response flags sent by the broker
        :param rc: stands for reasonCode, which is a code for the connection result
        :param properties: can be used in MQTTv5, but is optional
    """
    print("CONNACK received with code %s." % rc)


# with this callback you can see if your publish was successful
def on_publish(client, userdata, mid, properties=None):
    """
        Prints mid to stdout to reassure a successful publish ( used as callback for publish )
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param mid: variable returned from the corresponding publish() call, to allow outgoing messages to be tracked
        :param properties: can be used in MQTTv5, but is optional
    """
    print("mid: " + str(mid))


# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    """
        Prints a reassurance for successfully subscribing
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param mid: variable returned from the corresponding publish() call, to allow outgoing messages to be tracked
        :param granted_qos: this is the qos that you declare when subscribing, use the same one for publishing
        :param properties: can be used in MQTTv5, but is optional
    """
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


# print message, useful for checking if it was successful
def on_message(client, userdata, msg):
    """
        Prints a mqtt message to stdout ( used as callback for subscribe )
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param msg: the message with topic and payload
    """

    #print("message: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    if msg.topic == f"games/{lobby_name}/lobby" and msg.payload.startswith(b"Game Over"):
        print("Game Over: All coins have been collected")
        return
    elif msg.payload.startswith(b"Error: Lobby name not found"):
            print("Lobby has been deleted after the game ended")
            return
    if msg.topic == f"games/{lobby_name}/scores":
        try:
            scores_dict = json.loads(msg.payload)
            print("Scores:")
            for team, score in scores_dict.items():
                print(f"{team}: {score}")
        except json.JSONDecodeError as e:
            print("Error decoding JSON for scores:", e)
        return
    try:
        # Decoding the message payload from byte to JSON
        message_dict = json.loads(msg.payload)    
        # '{"teammateNames": ["Player1"], "teammatePositions": [[7, 9]], "enemyPositions": [[2, 3]], "currentPosition": [9, 9], "coin1": [[8, 4], [8, 6]], "coin2": [[7, 5], [9, 2], [9, 5]], "coin3": [], "walls": [[7, 7], [8, 7]]}'         
        if (msg.topic.endswith("/game_state")):
            # Extract relevant information from the game state message
            player_name = msg.topic.split("/")[-2]
            team_name = player_team_dict[player_name]
            current_position = message_dict.get('currentPosition', 'N/A')
            print(f"\n=== Message received on topic: {msg.topic} ===")
            print(f"Current Position: {current_position}")
            if player_name in prev_player_positions:
                update_team_map(team_name, prev_player_positions[player_name], 'free')
            prev_player_positions[player_name] = current_position
            update_team_map(team_name, message_dict.get('currentPosition'), 'player')
            teammates = ', '.join(message_dict.get('teammateNames', []))
            print(f"Teammates: {teammates if teammates else 'None'}")
            
            print("Teammate Positions:")
            if message_dict.get('teammatePositions'):
                for pos in message_dict['teammatePositions']:
                    print(f"  - {pos}")
                    update_team_map(team_name, pos, 'player')
            else:
                print("  None")
            
            print("Enemy Positions:")
            if message_dict.get('enemyPositions'):
                for pos in message_dict['enemyPositions']:
                    print(f"  - {pos}")
                    update_team_map(team_name, pos, 'player')
            else:
                print("  None")
            
            print("Coins:")
            coins_combined = {**{'Coin1': message_dict.get('coin1', [])}, **{'Coin2': message_dict.get('coin2', [])}, **{'Coin3': message_dict.get('coin3', [])}}
            for coin_type, positions in coins_combined.items():
                if positions:
                    for pos in positions:
                        print(f"  {coin_type} at: {pos}")
                        update_team_map(team_name, pos, 'coin')
                else:
                    print(f"  {coin_type}: None")
            
            print("Walls:")
            if message_dict.get('walls'):
                for wall in message_dict['walls']:
                    print(f"  - {wall}")
                    update_team_map(team_name, wall, 'wall')
            else:
                print("  None")
            
            # Update surrounding 5x5 grid centered at current player position to 'free' if the current value is 0
            if current_position != 'N/A':
                # Calculate the bounds of the 5x5 grid, ensuring they are within the map's boundaries
                x_center, y_center = current_position
                x_min, x_max = max(x_center - 2, 0), min(x_center + 2, 9)
                y_min, y_max = max(y_center - 2, 0), min(y_center + 2, 9)

                for i in range(x_min, x_max + 1):
                    for j in range(y_min, y_max + 1):
                        if team_maps[team_name][i][j] == state_mapping['unexplored']:
                            update_team_map(team_name, [i, j], 'free')
                            
            print_map(team_maps[team_name])

    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)
    except KeyError as e:
        print(f"Key error: {e} - message format might have changed or is incorrect.")

def manhattan_distance(coord1, coord2) -> int:
    return abs(coord1[0] - coord2[0]) + abs(coord1[1] - coord2[1])

def euclidean_distance(coord1, coord2):
    # returns square of distance
    return (coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2

def is_path_clear(team_map, current_position, target_coin):
    rows, cols = len(team_map), len(team_map[0])
    visited = set()
    queue = deque([(current_position, [])])  # (position, path)

    while queue:
        position, path = queue.popleft()
        if position == target_coin:
            return True
        if position in visited:
            continue
        visited.add(position)

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            new_x, new_y = position[0] + dx, position[1] + dy
            if 0 <= new_x < rows and 0 <= new_y < cols:
                if team_map[new_x][new_y] not in [state_mapping['wall'], state_mapping['player'], state_mapping['unexplored']]:
                    queue.append(((new_x, new_y), path + [(new_x, new_y)]))

    return False

def find_path_to_coin(team_map, start, end):
    rows, cols = len(team_map), len(team_map[0])
    open_set = {start}
    came_from = {}
    g_score = {start: 0}
    f_score = {start: manhattan_distance(start, end)}

    while open_set:
        current = min(open_set, key=lambda x: f_score[x])
        if current == end:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return path

        open_set.remove(current)
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            neighbor = (current[0] + dx, current[1] + dy)
            if 0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols:
                if team_map[neighbor[0]][neighbor[1]] in [state_mapping['wall'], state_mapping['player'], state_mapping['unexplored']]:
                    continue
                tentative_g_score = g_score[current] + 1
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = g_score[neighbor] + manhattan_distance(neighbor, end)
                    if neighbor not in open_set:
                        open_set.add(neighbor)

    return None

def find_nearest_unexplored_cell(team_map, start):
    rows, cols = len(team_map), len(team_map[0])
    open_set = {start}
    came_from = {}
    g_score = {start: 0}

    while open_set:
        current = min(open_set, key=lambda x: g_score[x])
        if team_map[current[0]][current[1]] == state_mapping['unexplored']:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return path

        open_set.remove(current)
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            neighbor = (current[0] + dx, current[1] + dy)
            if 0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols:
                if team_map[neighbor[0]][neighbor[1]] in [state_mapping['wall'], state_mapping['player']]:
                    continue
                tentative_g_score = g_score[current] + 1
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    if neighbor not in open_set:
                        open_set.add(neighbor)

    return None

def find_next_move(player_name, team_name, current_position):
    team_map = team_maps[team_name]
    current_position = tuple(current_position)
    valid_moves = []

    # Check for walls and players in the adjacent cells
    for move, (dx, dy) in zip(["UP", "DOWN", "LEFT", "RIGHT"], [(-1, 0), (1, 0), (0, -1), (0, 1)]):
        new_x, new_y = current_position[0] + dx, current_position[1] + dy
        if 0 <= new_x < 10 and 0 <= new_y < 10:
            if team_map[new_x][new_y] not in [state_mapping['wall'], state_mapping['player'], state_mapping['unexplored']]:
                valid_moves.append((move, (new_x, new_y)))

    if not valid_moves:
        return None

    # Find the nearest coin based on Manhattan distance and coin value
    coins = []
    for i in range(10):
        for j in range(10):
            if team_map[i][j] == state_mapping['coin']:
                coins.append(((i, j), manhattan_distance(current_position, (i, j))))
    
    if coins:
        print(f"coins coords with dist = {coins}")

        # Check if the player is stuck in a loop
        if current_position in list(player_move_history[player_name])[-5:]:
            print("Player is stuck in a loop. Finding an alternative path.")
            # Find the nearest unexplored cell 
            path_to_unexplored = find_nearest_unexplored_cell(team_map, current_position)
            if path_to_unexplored:
                next_position = path_to_unexplored[1]
                for move, (dx, dy) in zip(["UP", "DOWN", "LEFT", "RIGHT"], [(-1, 0), (1, 0), (0, -1), (0, 1)]):
                    if (current_position[0] + dx, current_position[1] + dy) == next_position:
                        best_move = move
                        break
            else:
                # If no unexplored cells found, choose a random valid move
                best_move = random.choice(valid_moves)[0]
        else:
            # Find the shortest path to the target coin
            target_coin = min(coins, key=lambda x: x[1])
            path_to_coin = find_path_to_coin(team_map, current_position, target_coin[0])
            if path_to_coin:
                next_position = path_to_coin[1]
                for move, (dx, dy) in zip(["UP", "DOWN", "LEFT", "RIGHT"], [(-1, 0), (1, 0), (0, -1), (0, 1)]):
                    if (current_position[0] + dx, current_position[1] + dy) == next_position:
                        best_move = move
                        break
            else:
                # If no path to the target coin found, explore the nearest unexplored cell
                path_to_unexplored = find_nearest_unexplored_cell(team_map, current_position)
                if path_to_unexplored:
                    next_position = path_to_unexplored[1]
                    for move, (dx, dy) in zip(["UP", "DOWN", "LEFT", "RIGHT"], [(-1, 0), (1, 0), (0, -1), (0, 1)]):
                        if (current_position[0] + dx, current_position[1] + dy) == next_position:
                            best_move = move
                            break
                else:
                    # If no path to unexplored cells found, choose a random valid move
                    best_move = random.choice(valid_moves)[0]

    else:
        # If no coins found, explore the nearest unexplored cell 
        path_to_unexplored = find_nearest_unexplored_cell(team_map, current_position)
        if path_to_unexplored:
            next_position = path_to_unexplored[1]
            for move, (dx, dy) in zip(["UP", "DOWN", "LEFT", "RIGHT"], [(-1, 0), (1, 0), (0, -1), (0, 1)]):
                if (current_position[0] + dx, current_position[1] + dy) == next_position:
                    best_move = move
                    break
        else:
            # If no path to unexplored cells found, choose a random valid move
            best_move = random.choice(valid_moves)[0]

    # Add the current position to the player's move history
    player_move_history[player_name].append(current_position)

    return best_move

if __name__ == '__main__':
    load_dotenv(dotenv_path='./credentials.env')
    
    broker_address = os.environ.get('BROKER_ADDRESS')
    broker_port = int(os.environ.get('BROKER_PORT'))
    username = os.environ.get('USER_NAME')
    password = os.environ.get('PASSWORD')

    client = paho.Client(paho.CallbackAPIVersion.VERSION1, client_id="Player1", userdata=None, protocol=paho.MQTTv5)
    
    # enable TLS for secure connection
    client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    # set username and password
    client.username_pw_set(username, password)
    # connect to HiveMQ Cloud on port 8883 (default for MQTT)
    client.connect(broker_address, broker_port)
    print("PlayerClient connec+ted to broker")
    # setting callbacks, use separate functions like above for better visibility
    client.on_subscribe = on_subscribe # Can comment out to not print when subscribing to new topics
    client.on_message = on_message
    client.on_publish = on_publish # Can comment out to not print when publishing to topics

    lobby_name = "TestLobby"
    player_1 = "Player1"
    player_2 = "Player2"
    player_3 = "Player3"
    player_4 = "Player4"
    print("Initialized lobby name and player strings")
    client.subscribe(f"games/{lobby_name}/lobby")
    client.subscribe(f'games/{lobby_name}/+/game_state')
    client.subscribe(f'games/{lobby_name}/scores')
    
    # Create an empty map for each team
    team_maps['ATeam'] = create_empty_map()
    team_maps['BTeam'] = create_empty_map()
    player_team_dict[player_1] = 'ATeam'
    player_team_dict[player_2] = 'ATeam'
    player_team_dict[player_3] = 'BTeam'
    player_team_dict[player_4] = 'BTeam'
    # Initialize the move history for each player
    player_move_history[player_1] = deque(maxlen=10)
    player_move_history[player_2] = deque(maxlen=10)
    player_move_history[player_3] = deque(maxlen=10)
    player_move_history[player_4] = deque(maxlen=10)
    
    client.publish("new_game", json.dumps({'lobby_name':lobby_name,
                                            'team_name':'ATeam',
                                            'player_name' : player_1}))
    
    client.publish("new_game", json.dumps({'lobby_name':lobby_name,
                                            'team_name':'ATeam',
                                            'player_name' : player_2}))
    
    client.publish("new_game", json.dumps({'lobby_name':lobby_name,
                                        'team_name':'BTeam',
                                        'player_name' : player_3}))
    client.publish("new_game", json.dumps({'lobby_name':lobby_name,
                                        'team_name':'BTeam',
                                        'player_name' : player_4}))

    print("Published new game")
    time.sleep(1) # Wait a second to resolve game start
    client.publish(f"games/{lobby_name}/start", "START")
    
    # Starting the MQTT client loop in a separate thread to allow for asynchronous operation
    client.loop_start()

    players = [player_1, player_2, player_3, player_4]#, player_2, player_3]
    valid_moves = ["UP", "DOWN", "LEFT", "RIGHT"]

    try:
        while True:
            for player in players:  
                time.sleep(0.5)              
                team_name = player_team_dict[player]
                current_position = prev_player_positions.get(player)
                
                if current_position is not None and team_name is not None:
                    next_move = find_next_move(player, team_name, current_position)
                    
                    if next_move:
                        # Publishing the player's move to the broker
                        # print(f"Algo Output: {next_move}")
                        # if input("Cool? ") != 'N':
                        client.publish(f"games/{lobby_name}/{player}/move", next_move)
                            # print(f"Move {next_move} sent for {player}")
                    else:
                        print(f"No valid move found for {player}")
                else:
                    print(f"Current position not available for {player}")
            
            # Add a delay if necessary, for example, to wait for all moves to be processed
            # time.sleep(1)
    
    except KeyboardInterrupt:
        print("Game interrupted by user.")

    finally:
        # Optionally: publish a STOP command to end the game
        client.publish(f"games/{lobby_name}/start", "STOP")
        # Stopping the MQTT client loop to cleanly shutdown
        client.loop_stop()
        print("Game ended.")