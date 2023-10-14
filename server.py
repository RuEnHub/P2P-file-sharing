from functions import get_ip, send_list
import socket
import threading

server_ip = get_ip()
server_port = 9999
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((server_ip, server_port))
server.listen(5)

clients_info = {} # {'client_socket' : ('client_listen_ip', 'client_listen_port')}


def get_connected_clients(client_socket):
    return [value for key, value in clients_info.items() if key != client_socket]


def handle_client(client_socket):
    while True:
        try:
            command = client_socket.recv(1024).decode()

            if command.startswith("LISTEN"):
                parts = command.split()
                client_listen_ip = parts[1]
                client_listen_port = int(parts[2])
                clients_info[client_socket] = (client_listen_ip, client_listen_port)
            if command == "USERS":
                other_clients = get_connected_clients(client_socket)
                send_list(client_socket, other_clients)
            elif command == "DISCONNECT":
                print("Соединение с клиентом разорвано")
                del clients_info[client_socket]
                client_socket.close()
                break

        except Exception as e:
            print(str(e))
            del clients_info[client_socket]
            client_socket.close()
            break

while True:
    client, addr = server.accept()
    print(f"Принято входящее соединение от {addr}")
    client_thread = threading.Thread(target=handle_client, args=(client,))
    client_thread.start()
    