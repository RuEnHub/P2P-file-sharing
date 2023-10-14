import socket
import json

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    print(f"Ваш IP {IP}")
    return IP

def receive_list(client_socket):
    data_json = client_socket.recv(1024).decode()
    data_list = json.loads(data_json)
    return data_list

def send_list(client_socket, data_list):
    data_json = json.dumps(data_list)
    client_socket.send(data_json.encode())

def read_int(str):
	while True:
	    try:
	        number = int(input(str))
	        return number
	    except Exception as e:
	        pass
	        