import socket
from threading import Thread
import os

# Server connection setup
host_name = socket.gethostname()
server_ip = socket.gethostbyname(host_name)
port = 18000

# File paths for downloads
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)


def receive_messages(client_socket):
    """Receive messages from the server."""
    while True:
        try:
            msg = client_socket.recv(1024).decode()
            if msg.startswith("FILE:"):
                # Process a file message
                filename = msg.split(":")[1]
                receive_file(client_socket, filename)
            else:
                print(msg)
        except Exception as e:
            print("Error receiving message:", e)
            client_socket.close()
            break


def receive_file(client_socket, filename):
    """Receive and save a file from the server."""
    print("receiving file")
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
    with open(filepath, 'wb') as f:
        data = client_socket.recv(1024)
        f.write(data)
        print(f)

    print(f"File {filename} downloaded and saved in {DOWNLOAD_FOLDER}")


def send_file(client_socket, filepath):
    try:
        filename_header = f"FILE:{os.path.basename(filepath)}"
        client_socket.send(filename_header.encode())

        with open(filepath, 'r') as f:
            while data := f.read():
                client_socket.send(data.encode())
        print(f"File {filepath} sent to the server.")

    except FileNotFoundError:
        print("File not found.")


def main_menu():
    print("\n1. View Active Users\n2. Join Chatroom\n3. Quit")
    return input("Choose an option: ")


def main():

    while True:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, port))
        choice = main_menu()

        if choice == '1':
            client_socket.send("VIEW_ACTIVE_USERS".encode())
            try:
                response = client_socket.recv(1024).decode()
                if response == "NO_ACTIVE_USERS":
                    print("No active users currently.")
                else:
                    print(response)
            except Exception as e:
                print(f"Error receiving active users: {e}")
                break

        elif choice == '2':
            username = input("Enter a username: ")
            client_socket.send(username.encode())
            try:
                response = client_socket.recv(1024).decode()
                if "Username already in use" in response or "Chatroom is full" in response:
                    print(response)
                    continue
                else:
                    print(response)
                    print("Connected to the chatroom!")
                    break  # Exit to start messaging
            except Exception as e:
                print(f"Error receiving server response: {e}")
                break


        elif choice == '3':
            print("Exiting the program.")
            client_socket.send("q".encode())
            client_socket.close()

            return


    # Start a thread to listen for messages from the server
    Thread(target=receive_messages, args=(client_socket,), daemon=True).start()

    # Chatroom interaction
    while True:
        msg = input()

        if msg.lower() == 'q':
            client_socket.send(msg.encode())
            print("Exiting chatroom...")
            client_socket.close()
            break
        elif msg.lower() == 'a':
            # File upload option
            filepath = input("Please enter the file path and name: ")
            send_file(client_socket, filepath)
        else:
            client_socket.send(msg.encode())


if __name__ == "__main__":
    main()
