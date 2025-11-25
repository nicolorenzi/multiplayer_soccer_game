from socket import *
import threading
import json
import time

# game state
player_positions = {
    1: [100, 300],
    2: [800, 300]
}
ball_position = [450, 300]
score = [0, 0]
ball_velocity = [0, 0]

player_inputs = {
    1: {"up": False, "down": False, "left": False, "right": False},
    2: {"up": False, "down": False, "left": False, "right": False},
}

clients = {}
state_lock = threading.Lock()


def handle_client(connectionSocket, addr, player_id):
    print(f'Connection from {addr} has been established. Assigned Player ID: {player_id}')
    
    try:
        while True:
            request = connectionSocket.recv(1024).decode()
            if not request:
                break
            print(f'Player {player_id} says: {request}')
            try:
                inputs = json.loads(request)
                with state_lock:
                    player_inputs[player_id] = inputs
            except:
                print(f"Invalid JSON from Player {player_id}")

            #echo back (can remove if needed)
            # response = f'Echo from server to Player {player_id}: {request}'
            # connectionSocket.send(response.encode())

    except Exception as e:
        print(f'An error occurred with Player {player_id}: {e}')

    finally:
        connectionSocket.close()
        print(f'Connection with Player {player_id} closed.')


def update_game_state():
    speed = 5

    # move players
    for pid in [1, 2]:
        inp = player_inputs[pid]
        x, y = player_positions[pid]

        if inp["up"]:
            y -= speed
        if inp["down"]:
            y += speed
        if inp["left"]:
            x -= speed
        if inp["right"]:
            x += speed

        x = max(20, min(880, x))
        y = max(20, min(580, y))

        player_positions[pid] = [x, y]

    # move ball
    global ball_position, ball_velocity

    # Ball momentum update
    ball_position[0] += ball_velocity[0]
    ball_position[1] += ball_velocity[1]

    # Ball friction
    ball_velocity[0] *= 0.95
    ball_velocity[1] *= 0.95

    # Bounce off walls
    if ball_position[0] <= 20 or ball_position[0] >= 880:
        ball_velocity[0] *= -1
    if ball_position[1] <= 20 or ball_position[1] >= 580:
        ball_velocity[1] *= -1

    # check if players kick the ball
    for pid in [1, 2]:
        px, py = player_positions[pid]
        bx, by = ball_position

        dx = bx - px
        dy = by - py
        dist = (dx**2 + dy**2) ** 0.5

        if dist < 40:  # player radius 20 + ball radius 12 ~ 32
            # push ball away from player
            ball_velocity[0] += dx * 0.1
            ball_velocity[1] += dy * 0.1


def broadcast_state():
    state = {
        "p1": player_positions[1],
        "p2": player_positions[2],
        "ball": ball_position,
        "score": score
    }

    msg = (json.dumps(state) + "\n").encode()

    for pid in clients:
        try:
            clients[pid].sendall(msg)
        except:
            pass


# main server
serverPort = 2525
serverSocket = socket(AF_INET, SOCK_STREAM)

serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

serverSocket.bind(('', serverPort))
serverSocket.listen(2)

print('The server is ready to receive')

#accept players 1 and 2
for player_id in [1, 2]:
    conn, addr = serverSocket.accept()
    clients[player_id] = conn

    #send player ID to client
    conn.send(json.dumps({"player_id": player_id}).encode())

    #start client thread
    client_thread = threading.Thread(
        target=handle_client,
        args=(conn, addr, player_id),
        daemon=True
    )
    client_thread.start()

print("Both players connected. Starting game...")

# 60 FPS game loop
while True:
    time.sleep(1/60)
    with state_lock:
        update_game_state()
        broadcast_state()
