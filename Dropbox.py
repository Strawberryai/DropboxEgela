import requests
import urllib
import webbrowser
from socket import AF_INET, socket, SOCK_STREAM
import json
import helper

app_key = '7u3tmn29kih8mst'
app_secret = 'rccw3i8guxcazjk'
server_addr = "localhost"
server_port = 3000
redirect_uri = "http://" + server_addr + ":" + str(server_port)
token_acceso='init'

class Dropbox:
   #_access_token=_access_token 
   _path = "/"
   _files = []
   _root = None
   _msg_listbox = None

   def __init__(self, root):
       self._root = root

   def local_server(self):
        # Crear servidor local que escucha por el puerto 8090
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind(('localHost', server_port))
        server_socket.listen(1)
        print("\tLocal server listening on port {server_port}")
        
        # Recibir la solicitude 302 del navegador
        client_connection, client_address = server_socket.accept()
        peticion = client_connection.recv(1024)
        print("\tRequest from the browser received at local server:")
        
        # Buscar en la petición el "auth_code"
        primera_linea = peticion.decode('UTF8').split('\n')[0]
        print("\t" + primera_linea)
        aux_auth_code = primera_linea.split(' ')[1]
        auth_code = aux_auth_code[7:].split('&')[0]
        print ("\tauth_code:" + auth_code)
        
        # Devolver una respuesta al usuario
        http_response = "HTTP/1.1 200 OK\r\n\r\n" \
        "<html>" \
        "<head><title>Auth_Code!</title></head>" \
        "<body>The authentication flow has completed. Close this window.</body>" \
        "</html>"
    
        client_connection.sendall(http_response.encode(encoding="utf-8"))
        client_connection.close()
        server_socket.close()

        # ACCESS TOKEN
        params = {'code': auth_code, 'grant_type': 'authorization_code', 'client_id': app_key, 'client_secret': app_secret, 'redirect_uri': redirect_uri}
        cabeceras={'User-Agent':'Python Client', 'Content-Type': 'application/x-www-form-urlencoded'}

        uri='https://api.dropboxapi.com/oauth2/token'
        respuesta = requests.post( uri, headers=cabeceras,data=params)
        print ("\t" + str(respuesta.status_code))
        json_respuesta = json.loads(respuesta.content)
        access_token = json_respuesta['access_token']
        print ("\tAccess_Token:"+ access_token)
        global _access_token
        _access_token=access_token
        return access_token

   def do_oauth(self):
        # Obtenemos la cookie de autorización para acceder a la API de Dropbox
        servidor = 'www.dropbox.com'

        params = {'response_type': 'code', 'client_id': app_key, 'redirect_uri': redirect_uri }
        params_encoded = urllib.parse.urlencode(params)
        recurso = '/oauth2/authorize?' + params_encoded

        uri = 'https://' + servidor + recurso
        webbrowser.open_new(uri)

        inst=self.local_server()
        
        self._root.destroy()
        

   def list_folder(self):
        print("/list_folder")
        uri = 'https://api.dropboxapi.com/2/files/list_folder'
        path = "/Aplicaciones"
        datos = {'path': ""}
        datos_encoded = json.dumps(datos)
        print("\tData: " + datos_encoded)
        print('Authorization Bearer '+ _access_token)
        cabeceras = {'Host': 'api.dropboxapi.com',
                    'Authorization': 'Bearer '+ _access_token,
                    'Content-Type': 'application/json'}
        respuesta = requests.post(uri, headers=cabeceras, data=datos_encoded, allow_redirects=False)
        status = respuesta.status_code

        print("\tStatus: " + str(status))
        contenido = respuesta.text
        print("\tContenido:" + str(contenido))
        contenido_json = json.loads(contenido)

        print("Ficheros en " + path)
        listaArchivos=[]
        for entrie in contenido_json["entries"]:
            print(entrie['name'])
            listaArchivos.append(entrie['name'])
        return(listaArchivos)
            

   def transfer_file(self, file_path, file_data):
       print("/upload")
       url = "https://content.dropboxapi.com/2/files/upload"

       headers = {
           "Authorization": "Bearer sl.BduVmI-7ff4RrpIVfwflBBiPe5v-79eynNgjRXulXtlvIj-njK1tOJr1V8J9oHnjaIW3FJmqYynQO2n5y4aohLvRYSZrBOPz_H9nCTrjtYu4MjfKo1ZprSZr278JfiePfRxZCKEG",
           "Content-Type": "application/octet-stream",
           "Dropbox-API-Arg": "{\"path\":\"" + file_path + "\"}"
       }

       data = file_data

       r = requests.post(url, headers=headers, data=data)

   def delete_file(self, file_path):
       print("/delete_file")
       url = "https://api.dropboxapi.com/2/files/delete_v2"

       headers = {
           "Authorization": "Bearer " +  _access_token,
           "Content-Type": "application/json"
       }

       data = {
           "path": file_path
       }

       r = requests.post(url, headers=headers, data=json.dumps(data))

   def create_folder(self, path):
       print("/create_folder")

       url = "https://api.dropboxapi.com/2/files/create_folder_v2"

       headers = {
           "Authorization": "Bearer " + _access_token,
           "Content-Type": "application/json"
       }

       data = {
           "path": path
       }

       r = requests.post(url, headers=headers, data=json.dumps(data))
