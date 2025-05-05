import socket
import threading
import json

host = 'localhost'
port = 23400

id = "Bar"
pedidoId = 1

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
receive_flag = True
time_time = 30

orders = {}
pending_order = {}

def start_client():
    client_socket.connect((host, port))
    client_socket.send(id.encode())
    threading.Thread(target=receive_message, args=(client_socket,), daemon=True).start()

def end_client():
    global receive_flag
    receive_flag = False
    for key in pending_order:
       pending_order[key]['Time'].cancel()
    client_socket.close()

def ressend_order(orderId):
    entry = pending_order[orderId]

    if not entry:
        return
    client_socket.send(entry['Message'].encode())

    timer = threading.Timer(time_time, ressend_order, args=(orderId))
    entry['Time'] = timer
    timer.start()

def order_ready(table, orderId):
    if table not in order:
        print("Não há pedidos para essa mesa")
        return
    for order in orders[table]:
        jsonOrder = json.loads(order)
        if int(orderId) == jsonOrder['Id']:
            msg = json.dumps({"Table": table, "Order": jsonOrder, "Tipe": "Ready", "From": "Bar"})
            client_socket.send(msg.encode())

            if orderId not in pending_order:
                timer = threading.Timer(time_time, ressend_order, args=(orderId))
                pending_order[orderId] = {'Time': timer, 'Message': msg}
                timer.start()
        print(f'Pedido {order} está pronto!')
    
def handle_order(msg):
    global pedidoId
    table = msg['Table']
    order = json.loads(msg['Order'][0])
    orderVector = json.dumps({
        'Item': order['Item'],
        'Amount': order['Amount'],
        'Id': pedidoId
    })
    pedidoId += 1
    if table not in orders:
        orders[table] = []
    orders[table].append(orderVector)
    print(f'Pedido {order} feito para mesa {table}!')

def handle_delivery(msg):
    table = msg['Table']
    orderId = msg['Id']
    if table not in orders:
        print("Não há pedidos para essa mesa")
        return
    for order in orders[table]:
        jsonOrder = json.loads(order)
        if int(orderId) == jsonOrder['Id']:
            orders[table].remove(order)
            break
    for key in pending_order:
        pending_order[key]['Time'].cancel()
    print(f'Pedido {orderId} para mesa {table} foi entregue!')

def receive_message(socket):
    while receive_flag:
        try:
            data = socket.recv(1024)
            if data:
                msg = json.loads(data.decode())
                match(msg['Tipe']):
                    case 'Order':
                        handle_order(msg)
                    case 'Delivery':
                        handle_delivery(msg)
                    case 'EndServer':
                        print(msg)
                    case _:
                        print(orders)
        except:
            break

if __name__ == "__main__":
    option = None
    start_client()
    while option != 0:
        print("O que deseja:")
        print("1 - Pedido Pronto")
        print("2 - Lista Pedidos")
        print("0 - Sair")
        
        try:
            option = int(input())
            if option == 1:
                table = input("Mesa: ")
                orderId = input("Pedido: ")
                order_ready(table, orderId)
            elif option == 2:
                print(orders)
            elif option == 0:
                end_client()
                print("Saindo...")
                break
            else:
                print("Comando não aceito")
        except ValueError:
            print("Por favor, insira um número válido.")