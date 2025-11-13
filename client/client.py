import socket
import json
import pygame
import threading

SERVER_IP = "127.0.0.1"
SERVER_PORT = 2525

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
PLAYER_RADIUS = 20
BALL_RADIUS = 12

COLOUR_FIELD = (34, 139, 34)
COLOUR_LINES = (255, 255, 255)
COLOUR_PLAYER1 = (0, 102, 255)
COLOUR_PLAYER2 = (255, 51, 51)
COLOUR_BALL = (255, 255, 255)
COLOUR_TEXT = (255, 255, 255)

# Socket init

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER_IP, SERVER_PORT))

# recieve player id
player_info = json.loads(client.recv(1024).decode())
PLAYER_ID = player_info["player_id"]
print(f"Connected as Player {PLAYER_ID}")

# shared game state
game_state = {
    "p1": [100, 300],
    "p2": [800, 300],
    "ball": [450, 300],
    "score": [0, 0]
}

state_lock = threading.Lock()

# background thread for revieving game stte
def listen_to_server():
    global game_state
    while True:
        try:
            data = client.recv(4096).decode()
            if not data:
                break
            new_state = json.loads(data)
            with state_lock:
                game_state = new_state
        
        except Exception as e:
            print(f"Server connection lost: {e}")
            break

listener_thread = threading.Thread(target=listen_to_server, daemon=True)
listener_thread.start()

# Pygame init
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Multiplayer Soccer - Player {player_id}".format(player_id=PLAYER_ID))
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 30)

#draw field


# main loop
running = True
while running:
    clock.tick(60)

    # handle input
    keys = pygame.key.get_pressed()
    inputs = {
        "up": keys[pygame.K_w] or keys[pygame.K_UP],
        "down": keys[pygame.K_s] or keys[pygame.K_DOWN],
        "left": keys[pygame.K_a] or keys[pygame.K_LEFT],
        "right": keys[pygame.K_d] or keys[pygame.K_RIGHT]
    }

    #sed input to server
    try:
        client.send(json.dumps(inputs).encode())
    except:
        print("Server closed connection.")
        running = False

    # drawing
    with state_lock:
        p1 = game_state["p1"]
        p2 = game_state["p2"]
        ball = game_state["ball"]
        score = game_state["score"]

    draw_field(screen)

    #players

    #ball

    #scoreboard

    #quit handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()

pygame.quit()
client.close()