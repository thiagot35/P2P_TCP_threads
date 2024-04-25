import socket
import json
import random
import threading

#Conexão na porta 1099 padrão
s = socket.socket()
port = int(input("Digite a porta deste servidor:\n"))
s.bind(('127.0.0.1',port))
s.listen(5)

#dicionário que armazena a lista de arquivos da rede por chave {arquivo : [(ip,porta)]}
historico = {}

def join_server(r_dict, hist):
    print(f"Peer {r_dict['ip_cliente']}:{r_dict['porta_cliente']} adicionado com arquivos {r_dict['arq']}")
    ip_cliente = r_dict['ip_cliente']
    porta_cliente = r_dict['porta_cliente']
    dict_cli = {files: (ip_cliente,porta_cliente) for files in r_dict['arq']}
    
    for chave in dict_cli:
        if chave not in hist:
            hist[chave] = []
        hist[chave].append(dict_cli[chave])

    print(hist) 
    resposta_cliente = json.dumps("JOIN_OK")
    return resposta_cliente, hist
    
def update_server(r_dict, hist):
    
    ip_cliente = r_dict['ip_cliente']
    porta_cliente = r_dict['porta_cliente']
    #dict_cli = {files: r_dict['porta_cliente'] for files in r_dict['arq']}
    dict_cli = {files: (ip_cliente,porta_cliente) for files in r_dict['arq']}
    for chave in dict_cli:
        if chave not in hist:
            hist[chave] = []
        hist[chave].append(dict_cli[chave])

    resposta_cliente = json.dumps("UPDATE_OK")
    print(resposta_cliente)
    return resposta_cliente

def search_server(r_dict, hist):
    print(f"Peer {r_dict['ip_cliente']}:{r_dict['porta_cliente']} solicitou o arquivo: {r_dict['arq']}")
    try:
        resp_cliente = hist[r_dict['arq']]
    except:
        resp_cliente = []
    resposta_cliente = json.dumps(resp_cliente)
    return resposta_cliente
    
def thread_req(conn, ip, porta, hist):
    req = conn.recv(1024)
    req_dict = json.loads(req.decode())

    
    if req_dict['tipo_req'] == 'JOIN':
        json_resp, hist = join_server(req_dict, hist)           
            
                   
    elif req_dict['tipo_req'] == 'SEARCH':

        json_resp = search_server(req_dict, hist)
    
    elif req_dict['tipo_req'] == 'UPDATE':

        json_resp = update_server(req_dict, hist)
            
    for item in hist:
        hist[item] = list(set(hist[item]))
    #print("O histórico atualizado é: ", hist)
    conn.send(json_resp.encode())
    conn.close()
    
#Loop do servidor onde há sempre uma conexão em aberto para recebimento das requisições, todo o processo é feito em threads   
while True:
    print("iniciou")
      
    c, addr = s.accept()
    #print("Got connection from: ", addr)
    #print ("O c é: ", c)
    
    threading.Thread(target=thread_req,args=(c, addr[0], addr[1], historico)).start()