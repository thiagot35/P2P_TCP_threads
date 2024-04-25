import socket
import os
import json
import pandas as pd
import threading


caminho_pasta = str(input("Digite a pasta do cliente\n"))


# Lista todos os arquivos e diretórios no caminho fornecido
conteudo_pasta = os.listdir(caminho_pasta)

# Filtra apenas os arquivos, excluindo os diretórios
arquivos = [arquivo for arquivo in conteudo_pasta if os.path.isfile(os.path.join(caminho_pasta, arquivo))]

#variável para validar se este peer já está conectado à rede
join_ok = ""

#porta conhecida do Servidor
port = 1099

#porta deste cliente/peer
c_server = socket.socket()
port_c_server = int(input("Digite a porta deste cliente:\n"))
c_server.bind(('127.0.0.1',port_c_server))
c_server.listen(5)
ip_port_c_server = c_server.getsockname()

#classe de thread que após o Join na rede ficará sempre aguardando uma conexão de outro peer para enviar um arquivo
def thread_cserver_download(c, addr): 
    req = c.recv(1024)
    arq_download = json.loads(req.decode())
    #print(f"O cliente {addr} quer baixar o arquivo {arq_download}")
    
    filepath_download = caminho_pasta + "\\" + arq_download
    with open(filepath_download, 'rb') as file:
        # Lê o conteúdo do arquivo
        arquivo_mp4 = file.read()
    
     # Envia o tamanho do arquivo para o cliente
    len_arq = len(arquivo_mp4)
    c.send(str(len_arq).encode())

    # Envia os dados do arquivo para o cliente em partes
    for i in range(0, len_arq, 1024):
        c.send(arquivo_mp4[i:i+1024])
    
    #c.send(json_resp.encode())
    c.close()
 
#Classe que chama a classe de thread acima 
def cliente_servidor_download():
    c, addr = c_server.accept()
    thread_cserver_download(c, addr)

#Função Join    
def join_func(arquivos, ip_port_cserver, conn):
    dict_envio = {'tipo_req': 'JOIN', 'arq': arquivos, 'ip_cliente': ip_port_cserver[0], 'porta_cliente': ip_port_cserver[1]}
    json_envio = json.dumps(dict_envio)

    #ETAPA DE ENVIO
    bytes_envio = json_envio.encode()
    conn.send(bytes_envio)

    #RESPOSTA "JOIN_OK" RECEBIDA VINDA DO SERVIDOR
    resposta_servidor = json.loads(conn.recv(1024).decode())
    print(resposta_servidor)

    if resposta_servidor == "JOIN_OK":
        print(f"Sou peer {ip_port_cserver[0]}:{ip_port_cserver[1]} com arquivos {arquivos}")
      
    return resposta_servidor
 
#Função Update 
def update_func(arquivo, ip_port_cserver):
    dict_envio = {'tipo_req': 'UPDATE', 'arq': [arquivo], 'ip_cliente': ip_port_cserver[0], 'porta_cliente': ip_port_cserver[1]}
    json_envio = json.dumps(dict_envio)

    conn_update = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn_update.connect(('127.0.0.1', port))
    
    #ETAPA DE ENVIO
    bytes_envio = json_envio.encode()
    conn_update.send(bytes_envio)

    #RESPOSTA "UPDATE_OK" RECEBIDA VINDA DO SERVIDOR
    resposta_servidor = json.loads(conn_update.recv(1024).decode())
    
    conn_update.close()
    

#Função Search     
def search_func(ip_port_cserver, conn):
    arq_search = str(input("Qual arquivo gostaria de procurar?"))
    dict_envio = {'tipo_req': 'SEARCH', 'arq':arq_search, 'ip_cliente': ip_port_cserver[0], 'porta_cliente': ip_port_cserver[1]}
    json_envio = json.dumps(dict_envio)
    
    #ETAPA DE ENVIO
    bytes_envio = json_envio.encode()
    conn.send(bytes_envio)

    #RESPOSTA COM A LISTA DE PEERS QUE POSSUEM O ARQUIVO PROCURADO RECEBIDA VINDA DO SERVIDOR
    resposta_servidor = json.loads(conn.recv(1024).decode())
    return arq_search, resposta_servidor
 
#Função Download 
def download_func(ip_port_cserver, conn):
    arq_download, resp_search = search_func(ip_port_cserver, conn)
    #print("Arquivo de download: ", arq_download)
    #print("resp_search: ", resp_search)
    if len(resp_search) > 0:
        peer_server = resp_search[0]
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((peer_server[0], peer_server[1]))
        #ETAPA DE ENVIO
        
        
        json_envio = json.dumps(arq_download)
        bytes_envio = json_envio.encode()
        s.send(bytes_envio)


        
        #RESPOSTA RECEBIDA VINDA DO SERVIDOR
        len_arq = int(s.recv(1024).decode())
        
        filepath_download = caminho_pasta + "\\" + arq_download
        
        # Recebe os dados do arquivo em partes e salva no disco
        with open(filepath_download, 'wb') as file:
            while len_arq > 0:
                arq_mp4 = s.recv(1024)
                file.write(arq_mp4)
                len_arq -= len(arq_mp4)
 
        print(f"Arquivo {arq_download} baixado com sucesso na pasta {caminho_pasta}")
        #print("Fazendo Update")
        update_func(arq_download, ip_port_cserver)


#While que mantém o peer em funcionamento
while True:    
    print("Iniciando")   
    
    #Liga o servidor para recebimento de requisições de download apenas após ter feito o Join na rede
    if join_ok == "JOIN_OK":
        threading.Thread(target=cliente_servidor_download).start()

    
    req = str(input("Qual tipo de requisição gostaria de fazer? \n1) JOIN\n2) SEARCH\n3) DOWNLOAD\n\n")).upper()

    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', port))
    
    if req == 'JOIN':
        #Faz a conexão com o servidor e recebe o "JOIN_OK"
        join_ok = join_func(arquivos, ip_port_c_server,s)

    elif req == 'SEARCH':
        arq_search, resp_search = search_func(ip_port_c_server, s)
        print(f"Peers com arquivo {arq_search} solicitado: {resp_search}")
    elif req == 'DOWNLOAD':
        download_func(ip_port_c_server, s)
        
    
    s.close()
    
