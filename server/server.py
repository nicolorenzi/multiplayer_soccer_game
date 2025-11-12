from socket import *
import threading

def handle_client(connectionSocket, addr, player_id):
    print(f'Connection from {addr} has been established. Assigned Player ID: {player_id}')
    try:
        while True:
            request = connectionSocket.recv(1024).decode()
            if not request:
                break
            print(f'Player {player_id} says: {request}')
            response = f'Echo from server to Player {player_id}: {request}'
            connectionSocket.send(response.encode())
    except Exception as e:
        print(f'An error occurred with Player {player_id}: {e}')
    finally:
        connectionSocket.close()
        print(f'Connection with Player {player_id} closed.')


serverPort = 2525
serverSocket = socket(AF_INET, SOCK_STREAM)

serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

serverSocket.bind(('', serverPort))
serverSocket.listen(1)
print('The server is ready to receive')

while True:
    connectionSocket, addr = serverSocket.accept()

    client_thread = threading.Thread(target=handle_client, args=(connectionSocket, addr), daemon=True)
    client_thread.start()