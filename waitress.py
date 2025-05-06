import socket
import threading
import json

host = 'localhost'
port = 23400

id = input("Id do processo: ")

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
receive_flag = True

orders = {}
ready = {}

def start_client():
    client_socket.connect((host, port))
    client_socket.send(id.encode())
    threading.Thread(target=receive_message, args=(client_socket,), daemon=True).start()

def end_client():
    global receive_flag
    receive_flag = False
    client_socket.close()

def new_client():
    orders.clear()

def add_item(item, amount, tipe):
    strTipe = ""
    if tipe == 1:
        strTipe = "Kitchen"
    elif tipe == 2:
        strTipe = "Bar"
    else:
        print("Erro no tipo")
    order = json.dumps({"Item": item, "Amount": amount})
    if strTipe not in orders:
        orders[strTipe] = []
    orders[strTipe].append(order)

def send_order(table):
    msg = json.dumps({"Table": table, "Order": orders, "Tipe": "Order"})
    client_socket.send(msg.encode())
    new_client()

def handle_ready(msg):
    global ready
    table = msg['Table']
    order = msg['Order']
    readyVector = json.loads(json.dumps({
        'Item': order['Item'],
        'Amount': order['Amount'],
        'Id': order['Id'],
        'From': msg['From']
    }))
    if table not in ready:
        ready[table] = []
    for item in ready[table]:
        if item['Id'] == readyVector['Id']:
            print(ready)
            return
    ready[table].append(readyVector)
    print(ready)

def delivery_order(table, orderId):
    global ready
    if table not in ready:
        print("Não há pedido para essa mesa!")
    else:
        for item in ready[table]:
            if item['Id'] == int(orderId):
                delivery = json.dumps({
                    'Table': table,
                    'Id': orderId,
                    'From': item['From'],
                    'Tipe': 'Delivery'
                })
                client_socket.send(delivery.encode())
        print("Delivery")

def handle_finish(msg):
    global ready
    table = msg['Table']
    orderId = msg['Id']
    fromId = msg['From']
    if table not in ready:
        print("Pedido Inválido")
        return
    for item in ready[table]:
        if int(orderId) == item['Id'] and item['From'] == fromId:
            ready[table].remove(item)
            print(f'Pedido {orderId} entregue!')
            break

def receive_message(socket):
    while receive_flag:
        try:
            data = socket.recv(1024)
            if data:
                msg = json.loads(data.decode())
                match (msg['Tipe']):
                    case 'Finish':
                        handle_finish(msg)
                    case 'Ready':
                        handle_ready(msg)
                    case 'EndServer':
                        print(msg)
                    case _:
                        print(msg)
        except:
            break

def options_list():
    global ready
    option = None
    while option != 0:
        print("O que deseja:")
        print("1 - Adicionar Item.")
        print("2 - Fazer Pedido.")
        print("3 - Novo Atendimento.")
        print("4 - Entregar Pedido")
        print("5 - Pedidos Prontos")
        print("0 - Sair")
        
        try:
            option = int(input())
            if option == 1:
                print("1 - Comida")
                print("2 - Bebida")
                tipe = int(input())
                item = input("Item: ")
                amount = input("Quantidade: ")
                add_item(item, amount, tipe)
            elif option == 2:
                table = input("Mesa: ")
                print(orders)
                ok = input("Comfirma: (1-Sim,2-Não)")
                if ok == '1':
                    send_order(table)
            elif option == 3:
                new_client()
            elif option == 4:
                table = input("Mesa: ")
                orderId = input("Pedido: ")
                delivery_order(table, orderId)
            elif option == 5:
                print(ready)
            elif option == 0:
                end_client()
                print("Saindo...")
                break
            else:
                print("Comando não aceito")
        except ValueError:
            print("Por favor, insira um número válido.")

if __name__ == "__main__":
    start_client()
    options_list()