# Multiplayer Soccer Game

A simple real-time multiplayer soccer game built with Python, Sockets, and Pygame.  
Two clients connect to a central server, which manages player positions and broadcasts shared game state updates at 60 FPS.

---

## Features
- Two-player multiplayer over TCP.
- Real-time player movement using arrow keys.
- Centralized server managing game state.
- Pygame-based rendering.
- Threaded client listeners for smooth gameplay.

---

## Prerequisites
- **Python 3.6+** installed 
- **Pip** (Python package manager) installed
- 2 separate machines (recommended but not necessary)

You can verify using:

```bash
python3 --version
pip --version
```

## Run Steps
1. Clone the repository

```bash
git clone https://github.com/nicolorenzi/multiplayer_soccer_game.git
cd multiplayer_soccer_game
```

2. Create and activate a virtual environment

  **macOS/Linux**
  ```bash
  python3 -m venv env
  source env/bin/activate
  ```

  **Windows**
  ```bash
  python -m venv env
  env\Scripts\activate.bat
  ```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Update SERVER_IP constant in client.py to the server machine's IP address

   Can find IP address by running: 

**macOS/Linux**
```bash
ipconfig getifaddr en0
```
**Windows**
```bash
ipconfig
```

   Then update this line in client.py:
   ```python
   SERVER_IP = "xxx.xxx.xxx.xxx"
   ```

5. Open the 'server' directory and start the server in terminal

```bash
cd server
python3 server.py
```

6. In a second terminal, open the 'client' directory and start client 1 

```bash
cd client
python3 client.py
```

7. Repeat steps 1-3 on a second machine (OPTIONAL but recommended)

8. In another terminal, open the 'client' directory and start client 2

```bash
cd client
python3 client.py
```

Once each client connects, they should receive: 

```bash
Connected as Player 1
Connected as Player 2
```

---

## Limitations
- Supports only 2 players
- Both clients must be on the same local network
- No collisions between players yet
- P1 loads in slightly quicker than P2
