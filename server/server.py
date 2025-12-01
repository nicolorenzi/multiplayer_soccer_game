from socket import *
import threading
import json
import time

# Game State
player_positions = {
    1: [100, 300],
    2: [800, 300]
}
ball_position = [450, 300]
score = [0, 0]
ball_velocity = [0, 0]

player_inputs = {
    1: {"up": False, "down": False, "left": False, "right": False, "replay": False},
    2: {"up": False, "down": False, "left": False, "right": False, "replay": False},
}

clients = {}
state_lock = threading.Lock()

replay_votes = {1: False, 2: False}
quit_requested = False

def handle_client(connectionSocket, addr, player_id):
    global quit_requested
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
                    if inputs.get("replay", False):
                        replay_votes[player_id] = True
                    if inputs.get("quit", False):
                        quit_requested = True
                        print(f"Player {player_id} requested to quit")
            except:
                print(f"Invalid JSON from Player {player_id}")

    except Exception as e:
        print(f'An error occurred with Player {player_id}: {e}')

    finally:
        connectionSocket.close()
        print(f'Connection with Player {player_id} closed.')


def update_game_state():
    speed = 5

    # Moves players
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

    # Moves ball
    global ball_position, ball_velocity

    # Ball momentum update
    ball_position[0] += ball_velocity[0]
    ball_position[1] += ball_velocity[1]

    # Ball friction
    ball_velocity[0] *= 0.95
    ball_velocity[1] *= 0.95

    # Bounce off top and bottom walls
    if ball_position[1] <= 20 or ball_position[1] >= 580:
        ball_velocity[1] *= -1

    # Bounce off left and right walls (not in goal area)
    goal_top = 200
    goal_bottom = 400
    
    # Only bounce if not in goal zone
    if ball_position[1] < goal_top or ball_position[1] > goal_bottom:
        if ball_position[0] <= 20 or ball_position[0] >= 880:
            ball_velocity[0] *= -1

    # Checks if players kick the ball
    for pid in [1, 2]:
        px, py = player_positions[pid]
        bx, by = ball_position

        dx = bx - px
        dy = by - py
        dist = (dx**2 + dy**2) ** 0.5

        if dist < 40: 
            # Pushes ball away from player
            ball_velocity[0] += dx * 0.1
            ball_velocity[1] += dy * 0.1


def check_goal():
    global ball_position, ball_velocity, score
    
    # Goal dimensions
    goal_top = 200
    goal_bottom = 400
    left_goal_x = 20
    right_goal_x = 880
    
    bx, by = ball_position
    
    # Check if ball is in goal zone
    if goal_top <= by <= goal_bottom:
        # Player 2 scores (ball crossed left goal line)
        if bx <= left_goal_x:
            score[1] += 1
            print(f"GOAL! Player 2 scores! Score: {score[0]} - {score[1]}")
            reset_after_goal()
            return True
        
        # Player 1 scores (ball crossed right goal line)
        elif bx >= right_goal_x:
            score[0] += 1
            print(f"GOAL! Player 1 scores! Score: {score[0]} - {score[1]}")
            reset_after_goal()
            return True
    
    return False


def reset_after_goal():
    global ball_position, ball_velocity, player_positions
    
    # Reset ball
    ball_position = [450, 300]
    ball_velocity = [0, 0]
    
    # Reset players 
    player_positions[1] = [100, 300]
    player_positions[2] = [800, 300]
    
    print("Positions reset after goal")


def reset_game():
    global ball_position, ball_velocity, player_positions, score, replay_votes
    
    # Reset score
    score[0] = 0
    score[1] = 0
    
    # Reset ball
    ball_position = [450, 300]
    ball_velocity = [0, 0]
    
    # Reset players
    player_positions[1] = [100, 300]
    player_positions[2] = [800, 300]
    
    # Reset replay votes
    replay_votes[1] = False
    replay_votes[2] = False
    
    print("Game reset for replay!")


def check_game_over():
    if score[0] >= 3:
        return True, 1  # Player 1 wins
    if score[1] >= 3:
        return True, 2  # Player 2 wins
    
    return False, None


def check_replay_votes():
    return replay_votes[1] and replay_votes[2]


def broadcast_state(game_over=False, winner=None):
    state = {
        "p1": player_positions[1],
        "p2": player_positions[2],
        "ball": ball_position,
        "score": score,
        "game_over": game_over,
        "winner": winner,
        "replay_votes": replay_votes
    }

    msg = (json.dumps(state) + "\n").encode()

    for pid in clients:
        try:
            clients[pid].sendall(msg)
        except:
            pass


# Main Server
serverPort = 2525
serverSocket = socket(AF_INET, SOCK_STREAM)

serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

serverSocket.bind(('', serverPort))
serverSocket.listen(2)

print('The server is ready to receive')

# Accepts players 1 and 2
for player_id in [1, 2]:
    conn, addr = serverSocket.accept()
    clients[player_id] = conn

    conn.send(json.dumps({"player_id": player_id}).encode())

    client_thread = threading.Thread(
        target=handle_client,
        args=(conn, addr, player_id),
        daemon=True
    )
    client_thread.start()

print("Both players connected. Starting game...")

# 60 FPS game loop
game_running = True
game_over = False
winner = None

while game_running:
    time.sleep(1/60)

    with state_lock:
        # If game is over, check for replay votes or quit request
        if game_over:
            if quit_requested:
                print("Quit requested by a player. Shutting down server...")
                game_running = False
                break

            if check_replay_votes():
                print("Both players voted to replay!")
                reset_game()
                game_over = False
                winner = None
            broadcast_state(game_over=True, winner=winner)
        else:
            update_game_state()
            
            if check_goal():
                # Check if game is over
                is_over, game_winner = check_game_over()
                if is_over:
                    print(f"GAME OVER! Player {game_winner} wins with score {score[0]} - {score[1]}!")
                    game_over = True
                    winner = game_winner
            
            # Broadcast normal state
            broadcast_state(game_over=game_over, winner=winner)

serverSocket.close()