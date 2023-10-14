from functions import get_ip, send_list, receive_list, read_int
from progress.bar import IncrementalBar
import time
import socket
import threading
import sys
import os
import datetime

buffer_size = 4096
folder_output = os.getcwd() + "\\file\\"
folder_input = os.getcwd() + "\\download\\"

# Прослушка порта
client_listen_ip = get_ip()
client_listen_port = read_int("Введите прослушивающий порт: ")
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.bind((client_listen_ip, client_listen_port))
client_socket.listen(5)

# Подключение к серверу
server_ip = input("Введите IP сервера: ")
#server_ip = "192.168.3.3"
server_port = 9999
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (server_ip, server_port)
client.connect(server_address)
client.send(f"LISTEN {client_listen_ip} {client_listen_port}".encode())


def communicating_with_client(client_conn):
    try:
        command = client_conn.recv(1024).decode()        
        
        if command.startswith("SEARCH"):
            filename = command.split()[1]
            found_files = []
            # рекурсивный поиск файла по подстроке
            if os.path.exists(folder_output) and os.path.isdir(folder_output):
                for root, dirs, files in os.walk(folder_output):
                    for file in files:
                        if filename in file:
                            file_path = os.path.join(root, file)
                            file_mtime = os.path.getmtime(file_path)
                            file_mtime_str = datetime.datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d %H:%M:%S')
                            found_files.append([file_path, file_mtime_str])
            send_list(client_conn, found_files)
        elif command.startswith("DOWNLOAD"):
            # отправляем запрошенный файл
            file_to_send = command.split()[1]
            file_size = os.path.getsize(file_to_send)
            client_conn.send(str(file_size).encode())            
            with open(file_to_send, "rb") as file:
                data = file.read(buffer_size)
                while data:
                    client_conn.send(data)
                    data = file.read(buffer_size)
    except Exception as e:
        pass
    finally:
        client_conn.close()
    

def waiting_connections(client_conn):
    while True:
        client_connection, client_addr = client_socket.accept()
        client_handler = threading.Thread(target=communicating_with_client, args=(client_connection,))
        client_handler.daemon = True
        client_handler.start()


# запуск потока ожидающий и обрабатывающий подключения клиентов
comm_server_thread = threading.Thread(target=waiting_connections, args=(client,))
comm_server_thread.daemon = True
comm_server_thread.start()

# основной поток общающийся с сервером и клиентами
try:
    while True:
        os.system('cls')
        command = input("Введите команду (search <filename>/exit): ")

        if command.startswith("search"):
            filename = command.split(" ")[1]
            client.send("USERS".encode())
            clients_list = receive_list(client)

            list_files = [] # [((addr), path), ...]
            
            for addr in clients_list:
                print(addr)
                selected_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)               
                selected_client_socket.connect(tuple(addr))                
                selected_client_socket.send(f"SEARCH {filename}".encode())
                
                for file in receive_list(selected_client_socket):
                    path = file[0]
                    print(f"{len(list_files)} - {os.path.basename(path)} {file[1]}")
                    list_files.append((tuple(addr), path))
                print()   
                selected_client_socket.close()  
            try: # Выбор файла и его скачивание 
                download_index = read_int("Введите номер скачиваемого файла: ")
                if 0 <= download_index < len(list_files):
                    addr, filename = list_files[download_index]
                    selected_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
                    selected_client_socket.connect(addr)                
                    selected_client_socket.send(f"DOWNLOAD {filename}".encode())
                    file_size = int(selected_client_socket.recv(1024).decode()) # размер файла
                    bar = IncrementalBar('Processing', max=file_size//buffer_size)
                    with open(folder_input + os.path.basename(filename), "wb") as file:
                        while True:
                            data = selected_client_socket.recv(buffer_size)
                            if not data:
                                bar.finish()
                                break
                            file.write(data)
                            bar.next()
                    selected_client_socket.close()
                    print("\nФайл успешно скачан")
                else:
                    print("Возврат в главное меню")
                time.sleep(5)
            except Exception as e:
                print("\nФайл не скачан - раздающее устройство закрыло подключение")
                os.remove(folder_input + os.path.basename(filename))
                time.sleep(5)
            
        elif command == "exit":
            client.send("DISCONNECT".encode())
            break
except KeyboardInterrupt:
        client.send("DISCONNECT".encode())
        print("Соединение прервано")
except Exception as e:
    print(str(e))
    client.send("DISCONNECT".encode())
    print("Соединение прервано")
finally:
    client.close()
