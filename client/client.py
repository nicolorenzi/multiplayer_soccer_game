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
buffer = ""

def listen_to_server():
    global game_state, buffer
    while True:
        try:
            chunk = client.recv(4096).decode()
            if not chunk:
                break

            buffer += chunk

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if line.strip():
                    new_state = json.loads(line)
                    with state_lock:
                        game_state = new_state

        except Exception as e:
            print(f"Server connection lost: {e}")
            break


# Pygame init
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(f"Multiplayer Soccer - Player {PLAYER_ID}")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 30)

#draw field
def draw_field(screen):
    screen.fill(COLOUR_FIELD)

    #midfeild line
    pygame.draw.line(screen, COLOUR_LINES, (SCREEN_WIDTH//2, 0), (SCREEN_WIDTH//2, SCREEN_HEIGHT), 5)

    #center circle
    pygame.draw.circle(screen, COLOUR_LINES, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2), 60, 3)

    #goals
    goal_height = 200
    pygame.draw.rect(screen, COLOUR_LINES, (0, (SCREEN_HEIGHT - goal_height)//2, 10, goal_height))
    pygame.draw.rect(screen, COLOUR_LINES, (SCREEN_WIDTH - 10, (SCREEN_HEIGHT - goal_height)//2, 10, goal_height))
    
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
    pygame.draw.circle(screen, COLOUR_PLAYER1, (int(p1[0]), int(p1[1])), PLAYER_RADIUS)
    pygame.draw.circle(screen, COLOUR_PLAYER2, (int(p2[0]), int(p2[1])), PLAYER_RADIUS)
    
    #ball
    pygame.draw.circle(screen, COLOUR_BALL, (int(ball[0]), int(ball[1])), BALL_RADIUS)
    
    #scoreboard
    score_text = font.render(f"Player 1: {score[0]}  Player 2: {score[1]}", True, COLOUR_TEXT)
    screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 20))
    
    #quit handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()

pygame.quit()
client.close()