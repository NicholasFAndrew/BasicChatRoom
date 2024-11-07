import socket
from ipaddress import ip_address
from threading import Thread
import os

# Create and bind a TCP server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_name = socket.gethostname()
s_ip = socket.gethostbyname(host_name)
port = 18000
server_socket.bind((host_name, port))

# Outputs bound contents
print("Socket Bound")
print("Server IP:", s_ip, "Server Port:", port)

# Listens for a set number of users
MAX_USERS = 3
server_socket.listen(MAX_USERS)

DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Client management
clients = {}  # Dictionary to map clients to usernames
msg_history = []  # Store chat history


# Function to handle each client
def client_handler(client_socket, client_address):
    while True:
        try:
            # Receive the username first to verify it
            username = client_socket.recv(1024).decode()

            if username == "VIEW_ACTIVE_USERS":
                send_active_users(client_socket)
            else:
                # Check if username is unique and max user limit is respected
                if len(clients) >= MAX_USERS:
                    client_socket.send("Chatroom is full. Please try again later.".encode())
                    client_socket.close()
                    return
                elif any(username.lower() == client[0].lower() for client in clients.values()):
                    client_socket.send("Username already in use. Please try another.".encode())
                    client_socket.close()
                    return
                else:
                    clients[client_socket] = (username, client_address)
                    print(f"{username} joined the chat.")

                    broadcast(f"{username} has joined the chat.", client_socket)
                    send_history(client_socket)
                    msg_history.append(f"{username} has joined the chat.")
                    break
        except Exception as e:
            print("Error:", e)
            client_socket.close()
            return

    # Main loop for receiving and forwarding messages
    while True:
        try:
            msg = client_socket.recv(1024).decode()
            if msg.lower() == 'q':
                username = clients[client_socket][0]
                msg_history.append(f"{username} has left the chat.")
                broadcast(f"{username} has left the chat.", client_socket)
                print(f"{username} has disconnected.")
                del clients[client_socket]
                client_socket.close()
                break
            else:
                if msg.startswith("FILE:"):
                    filename = msg.split(":")[1]
                    msg = receive_file(client_socket, filename)
                username = clients[client_socket][0]
                formatted_msg = f"{username}: {msg}"
                msg_history.append(formatted_msg)
                broadcast(formatted_msg, client_socket)
        except Exception as e:
            print(f"Error with client: {e}")
            if client_socket in clients:
                del clients[client_socket]
            client_socket.close()
            break


# Function to receive a file from a client and broadcast it
def receive_file(client_socket, filename):
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
    print(f"Receiving file {filename} and saving to {filepath}")

    # Open file to write binary data
    with open(filepath, 'wb') as f:
        data = client_socket.recv(1024)
        f.write(data)
        print("did I write the data?")

    with open(filepath, 'r') as f:
        return f.read()




# Function to broadcast a file to all clients
def broadcast_file(filepath):
    filename = os.path.basename(filepath)
    with open(filepath, 'rb') as f:
        file_data = f.read()

    for client in clients:
        client.send(f"FILE:{filename}".encode())
        client.send(file_data)
    print("Should be sending this: ", file_data.decode())
    broadcast(file_data.decode())

# Function to broadcast messages to all clients
def broadcast(message, sender_socket=None):
    for client in clients:
        client.send(message.encode())


# Send the chat history to a new client
def send_history(client_socket):
    if msg_history:
        client_socket.send("------Beginning of History--------\n".encode())
        for message in msg_history:
            client_socket.send((message + "\n").encode())
        client_socket.send("----------End of History----------\n".encode())


# Send active user list to requesting client
def send_active_users(client_socket):
    if not clients:
        client_socket.send("NO_ACTIVE_USERS".encode())
    else:
        active_users = "Active users:\n"
        for client, (username, address) in clients.items():

            active_users += f"Username: {username} IP and Port: {address}\n"
        client_socket.send(active_users.encode())


# Accept clients in the main server loop
print("Waiting for clients...")
while True:
    client_socket, client_address = server_socket.accept()
    print(f"{client_address} connected!")

    # Create a thread for each client connection
    client_thread = Thread(target=client_handler, args=(client_socket, client_address))
    client_thread.daemon = True
    client_thread.start()
