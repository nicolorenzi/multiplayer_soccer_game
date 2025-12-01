import socket
import json
import pygame
import threading

SERVER_IP = "10.0.0.9"
SERVER_PORT = 2525

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
PLAYER_RADIUS = 20
BALL_RADIUS = 12

COLOR_FIELD = (34, 139, 34)
COLOR_LINES = (255, 255, 255)
COLOR_PLAYER1 = (0, 102, 255)
COLOR_PLAYER2 = (255, 51, 51)
COLOR_BALL = (255, 255, 255)
COLOR_TEXT = (255, 255, 255)
COLOR_BUTTON = (100, 100, 100)
COLOR_BUTTON_HOVER = (150, 150, 150)
COLOR_BUTTON_VOTED = (50, 200, 50)
COLOR_QUIT_BUTTON = (200, 50, 50)  
COLOR_QUIT_HOVER = (255, 80, 80)   

# Socket init
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER_IP, SERVER_PORT))

# Recieve player id
player_info = json.loads(client.recv(1024).decode())
PLAYER_ID = player_info["player_id"]
print(f"Connected as Player {PLAYER_ID}")

# Shared game state
game_state = {
    "p1": [100, 300],
    "p2": [800, 300],
    "ball": [450, 300],
    "score": [0, 0],
    "game_over": False,
    "winner": None,
    "replay_votes": {1: False, 2: False}
}

waiting = True
state_lock = threading.Lock()

buffer = ""

def listen_to_server():
    global game_state, buffer, waiting
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
                        waiting = False

        except Exception as e:
            print(f"Server connection lost: {e}")
            break

listener = threading.Thread(target=listen_to_server, daemon=True)
listener.start()

# Pygame init
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(f"Multiplayer Soccer - Player {PLAYER_ID}")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 30)
button_font = pygame.font.SysFont("Arial", 25)

def draw_field(screen):
    screen.fill(COLOR_FIELD)

    # Midfield line
    pygame.draw.line(screen, COLOR_LINES, (SCREEN_WIDTH//2, 0), (SCREEN_WIDTH//2, SCREEN_HEIGHT), 5)

    # Center circle
    pygame.draw.circle(screen, COLOR_LINES, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2), 60, 3)

    # Goals
    goal_height = 200
    pygame.draw.rect(screen, COLOR_LINES, (0, (SCREEN_HEIGHT - goal_height)//2, 10, goal_height))
    pygame.draw.rect(screen, COLOR_LINES, (SCREEN_WIDTH - 10, (SCREEN_HEIGHT - goal_height)//2, 10, goal_height))


def draw_game_over(screen, winner, score, replay_votes, mouse_pos):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))
    
    game_over_font = pygame.font.SysFont("Arial", 60, bold=True)
    winner_font = pygame.font.SysFont("Arial", 40)
    score_font = pygame.font.SysFont("Arial", 35)
    
    game_over_text = game_over_font.render("GAME OVER", True, (255, 215, 0))
    winner_text = winner_font.render(f"Player {winner} Wins!", True, (255, 255, 255))
    final_score_text = score_font.render(f"Final Score: {score[0]} - {score[1]}", True, (255, 255, 255))
    
    screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, SCREEN_HEIGHT//2 - 120))
    screen.blit(winner_text, (SCREEN_WIDTH//2 - winner_text.get_width()//2, SCREEN_HEIGHT//2 - 40))
    screen.blit(final_score_text, (SCREEN_WIDTH//2 - final_score_text.get_width()//2, SCREEN_HEIGHT//2 + 20))
    
    # Button dimensions
    button_width = 180
    button_height = 50
    button_spacing = 20
    
    # Replay button
    replay_button_x = SCREEN_WIDTH//2 - button_width - button_spacing//2
    button_y = SCREEN_HEIGHT//2 + 80
    replay_button_rect = pygame.Rect(replay_button_x, button_y, button_width, button_height)
    
    # Check if this player has voted
    player_voted = replay_votes.get(str(PLAYER_ID), False) or replay_votes.get(PLAYER_ID, False)
    
    # Replay button color 
    if player_voted:
        replay_button_color = COLOR_BUTTON_VOTED
    elif replay_button_rect.collidepoint(mouse_pos):
        replay_button_color = COLOR_BUTTON_HOVER
    else:
        replay_button_color = COLOR_BUTTON
    
    pygame.draw.rect(screen, replay_button_color, replay_button_rect, border_radius=10)
    pygame.draw.rect(screen, COLOR_TEXT, replay_button_rect, 3, border_radius=10)
    
    if player_voted:
        replay_text = button_font.render("Waiting...", True, COLOR_TEXT)
    else:
        replay_text = button_font.render("Play Again", True, COLOR_TEXT)
    screen.blit(replay_text, (replay_button_x + button_width//2 - replay_text.get_width()//2, 
                               button_y + button_height//2 - replay_text.get_height()//2))
    
    # Quit button
    quit_button_x = SCREEN_WIDTH//2 + button_spacing//2
    quit_button_rect = pygame.Rect(quit_button_x, button_y, button_width, button_height)
    
    # Quit button color based on hover
    if quit_button_rect.collidepoint(mouse_pos):
        quit_button_color = COLOR_QUIT_HOVER
    else:
        quit_button_color = COLOR_QUIT_BUTTON
    
    pygame.draw.rect(screen, quit_button_color, quit_button_rect, border_radius=10)
    pygame.draw.rect(screen, COLOR_TEXT, quit_button_rect, 3, border_radius=10)
    
    quit_text = button_font.render("Quit", True, COLOR_TEXT)
    screen.blit(quit_text, (quit_button_x + button_width//2 - quit_text.get_width()//2, 
                            button_y + button_height//2 - quit_text.get_height()//2))
    
    # Vote status
    vote_text = button_font.render(f"Votes: {sum([1 for v in replay_votes.values() if v])}/2", True, COLOR_TEXT)
    screen.blit(vote_text, (SCREEN_WIDTH//2 - vote_text.get_width()//2, button_y + button_height + 20))
    
    return replay_button_rect, quit_button_rect  

    
# Main loop
running = True
replay_button_clicked = False
quit_button_clicked = False 

while running:
    clock.tick(60)
    mouse_pos = pygame.mouse.get_pos()

    # Get current game state
    with state_lock:
        p1 = game_state["p1"]
        p2 = game_state["p2"]
        ball = game_state["ball"]
        score = game_state["score"]
        game_over = game_state.get("game_over", False)
        winner = game_state.get("winner", None)
        replay_votes = game_state.get("replay_votes", {1: False, 2: False})

    # Handles input during game
    if not game_over:
        keys = pygame.key.get_pressed()
        inputs = {
            "up": keys[pygame.K_w] or keys[pygame.K_UP],
            "down": keys[pygame.K_s] or keys[pygame.K_DOWN],
            "left": keys[pygame.K_a] or keys[pygame.K_LEFT],
            "right": keys[pygame.K_d] or keys[pygame.K_RIGHT],
            "replay": False,
            "quit": False  
        }
        replay_button_clicked = False
        quit_button_clicked = False  
    else:
        # Send replay or quit vote if buttons were clicked
        inputs = {
            "up": False,
            "down": False,
            "left": False,
            "right": False,
            "replay": replay_button_clicked,
            "quit": quit_button_clicked  
        }

    # Send input to server
    try:
        client.send(json.dumps(inputs).encode())
    except:
        print("Server closed connection.")
        running = False

    # Waiting message
    if waiting:
        screen.fill(COLOR_FIELD)
        wait_text = font.render("Waiting for player 2...", True, COLOR_TEXT)
        screen.blit(wait_text, (SCREEN_WIDTH//2 - wait_text.get_width()//2, SCREEN_HEIGHT//2 - wait_text.get_height()//2))
    
    # Rest of game when done waiting 
    else: 
        draw_field(screen)

        # Players
        pygame.draw.circle(screen, COLOR_PLAYER1, (int(p1[0]), int(p1[1])), PLAYER_RADIUS)
        pygame.draw.circle(screen, COLOR_PLAYER2, (int(p2[0]), int(p2[1])), PLAYER_RADIUS)
    
        # Ball
        pygame.draw.circle(screen, COLOR_BALL, (int(ball[0]), int(ball[1])), BALL_RADIUS)
    
        # Scoreboard
        score_text = font.render(f"Player 1: {score[0]}  Player 2: {score[1]}", True, COLOR_TEXT)
        screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 20))
        
        # Draw game over screen if game ended
        if game_over and winner:
            replay_button_rect, quit_button_rect = draw_game_over(screen, winner, score, replay_votes, mouse_pos)
    
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and game_over:
            # Check if replay button was clicked
            if replay_button_rect and replay_button_rect.collidepoint(mouse_pos):
                replay_button_clicked = True
            # Check if quit button was clicked
            if quit_button_rect and quit_button_rect.collidepoint(mouse_pos):
                quit_button_clicked = True
                running = False  

    pygame.display.flip()

pygame.quit()
client.close()