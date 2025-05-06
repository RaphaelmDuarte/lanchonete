import socket
import threading
import json

host = 'localhost'
port = 23400

amount_clients = 10
clients = {}

orderId = 1

def handle_order(msg):
    global orderId
    table = msg['Table']
    orders = msg['Order']
    if 'Kitchen' in orders:
        kitchen_order = json.dumps({
            "Table": table,
            "Order": orders['Kitchen'],
            "Id": orderId,
            "Tipe": "Order"
        })
        clients["Kitchen"].send(kitchen_order.encode())

    if 'Bar' in orders:
        bar_order = json.dumps({
            "Table": table,
            "Order": orders['Bar'],
            "Id": orderId,
            "Tipe": "Order"
        })
        clients["Bar"].send(bar_order.encode())
    orderId += 1
    print(f'Pedido {orders} realizado!')

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
            print(f'Pedido {msg['Order']} pronto!')

def handle_delivery(msg):
    table = msg['Table']
    orderId = msg['Id']
    fromId = msg['From']
    print(fromId)
    order = json.dumps({
        'Table': table,
        'Id': orderId,
        'From': fromId,
        'Tipe': "Delivery"
    })
    match(fromId):
        case 'Kitchen':
            clients["Kitchen"].send(order.encode())
        case 'Bar':
            clients["Bar"].send(order.encode())
        case _:
            print("Erro no delivery!")
    print(f'Pedido {order} entregue!')

def handle_finish(msg):
    order = json.dumps(msg)
    for id in clients:
        if id != 'Kitchen' and id != 'Bar':
            clients[id].send(order.encode())
            print(f'Pedido {order} finalizado!')

def handle_client(conn, addr):
    id = conn.recv(1024).decode()
    if id in clients:
        print(f'Já há conexão com o id: {id}')
        return
    clients[id] = conn
    print(f"{id} conectado de {addr}")
    try:
        while True:
                data = conn.recv(1024)
                if not data:
                    print(f"[-] Cliente {addr} desconectado.")
                    break
                msg = json.loads(data.decode())
                match msg['Tipe']:
                    case 'Finish':
                        handle_finish(msg)
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
    finally:
        if id in clients:
            print(f"{id} foi desconetado!")
            del clients[id]
        conn.close()

def start_server():
    global amount_clients
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(amount_clients)
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