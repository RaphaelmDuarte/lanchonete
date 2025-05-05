import socket
import threading
import json

host = 'localhost'
port = 23400

clients = {}

def handle_order(msg):
    table = msg['Table']
    orders = msg['Order']
    if 'Kitchen' in orders:
        kitchen_order = json.dumps({
            "Table": table,
            "Order": orders['Kitchen'],
            "Tipe": "Order"
        })
        clients["Kitchen"].send(kitchen_order.encode())

    if 'Bar' in orders:
        bar_order = json.dumps({
            "Table": table,
            "Order": orders['Bar'],
            "Tipe": "Order"
        })
        clients["Bar"].send(bar_order.encode())

def handle_ready(msg):
    for id in clients:
        if id != 'Kitchen' and id != 'Bar':
            sendMsg = json.dumps({
                "Table": msg['Table'],
                "Order": msg['Order'],
                "Tipe": "Ready",
                "From": msg['From']
            })
            clients[id].send(sendMsg.encode())

def handle_delivery(msg):
    table = msg['Table']
    orderId = msg['Id']
    fromId = msg['From']
    print(fromId)
    order = json.dumps({
        'Table': table,
        'Id': orderId,
        'Tipe': "Delivery"
    })
    match(fromId):
        case 'Kitchen':
            print("Send to kitchen")
            clients["Kitchen"].send(order.encode())
        case 'Bar':
            print("Send to Bar")
            clients["Bar"].send(order.encode())
        case _:
            print("Erro no delivery!")
    print("Delivery")

def handle_client(conn, addr):
    id = conn.recv(1024).decode()
    clients[id] = conn
    print(f"{id} conectado de {addr}")
    try:
        while True:
                data = conn.recv(1024)
                if not data:
                    print(f"[-] Cliente {addr} desconectado.")
                    break
                msg = json.loads(data.decode())
                print(msg)
                match msg['Tipe']:
                    case 'Order':
                        handle_order(msg)
                    case 'Ready':
                        handle_ready(msg)
                    case 'Delivery':
                        handle_delivery(msg)
                    case _:
                        print(msg)

    except OSError as e:
        if e.errno == 10054:
           if id in clients:
            print(f"{id} foi desconetado!")
            del clients[id]
        conn.close() 
    except Exception as e:
        print(f"Erro com {addr}: {e}")

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print("Servidor aguardando conexões...")
    try:
        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\nServidor encerrado manualmente.")
    finally:
        for id in clients:
            clients[id].send(json.dumps({
                "de": "Servidor",
                "mensagem": "Servidor Encerrado!",
                'Tipe': 'EndServer'
            }).encode())
        server_socket.close()

if __name__ == "__main__":
    start_server()