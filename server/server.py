import socket
import threading
import json
import time

PORT = 2525

# Minimal game state
p1 = {"x": 100, "y": 300, "input": {}}
p2 = {"x": 800, "y": 300, "input": {}}
ball = {"x": 450, "y": 300, "vx": 0, "vy": 0}
score = [0, 0]

clients = {}
lock = threading.Lock()

def reset_ball():
    ball["x"], ball["y"] = 450, 300
    ball["vx"], ball["vy"] = 0, 0

def handle_client(conn, addr):
    global clients
    with lock:
        pid = 1 if 1 not in clients else 2
        clients[pid] = conn

    conn.send(json.dumps({"player_id": pid}).encode())

    try:
        while True:
            msg = conn.recv(1024)
            if not msg:
                break

            try:
                data = json.loads(msg.decode())
            except:
                continue

            with lock:
                if pid == 1:
                    p1["input"] = data
                else:
                    p2["input"] = data
    except:
        pass

    with lock:
        del clients[pid]
        print(f"Player {pid} disconnected")
    conn.close()


def update():
    # Player movement
    for p in (p1, p2):
        inp = p["input"]
        if inp.get("up"):    p["y"] -= 5
        if inp.get("down"):  p["y"] += 5
        if inp.get("left"):  p["x"] -= 5
        if inp.get("right"): p["x"] += 5

        # clamp
        p["x"] = max(20, min(880, p["x"]))
        p["y"] = max(20, min(580, p["y"]))

    # Move ball
    ball["x"] += ball["vx"]
    ball["y"] += ball["vy"]
    ball["vx"] *= 0.97
    ball["vy"] *= 0.97

    # Simple bounce
    if ball["y"] <= 10 or ball["y"] >= 590:
        ball["vy"] *= -1

    # Player → ball collision (simple push)
    for p in (p1, p2):
        dx = ball["x"] - p["x"]
        dy = ball["y"] - p["y"]
        dist = (dx*dx + dy*dy) ** 0.5
        if dist < 40:
            ball["vx"] += dx * 0.1
            ball["vy"] += dy * 0.1

    # Goals
    goal_top = 200
    goal_bottom = 400

    if ball["x"] < 10 and goal_top < ball["y"] < goal_bottom:
        score[1] += 1
        reset_ball()

    if ball["x"] > 890 and goal_top < ball["y"] < goal_bottom:
        score[0] += 1
        reset_ball()


def send_state():
    state = {
        "p1": [p1["x"], p1["y"]],
        "p2": [p2["x"], p2["y"]],
        "ball": [ball["x"], ball["y"]],
        "score": score
    }
    encoded = json.dumps(state).encode()
    for conn in clients.values():
        try:
            conn.sendall(encoded)
        except:
            pass


def game_loop():
    while True:
        time.sleep(1/60)
        with lock:
            update()
            send_state()


def main():
    threading.Thread(target=game_loop, daemon=True).start()

    s = socket.socket()
    s.bind(("", PORT))
    s.listen(2)
    print("Server running on port", PORT)

    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
