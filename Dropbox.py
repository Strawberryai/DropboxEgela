import requests
import urllib
import webbrowser
from socket import AF_INET, socket, SOCK_STREAM
import json
import helper

app_key = '7u3tmn29kih8mst'
app_secret = 'rccw3i8guxcazjk'
PORT            = 3000
redirect_uri    = f"http://localhost:{PORT}"

class Dropbox:
    _access_token = ""
    _path = ""
    _files = []
    _root = None
    _msg_listbox = None

    def __init__(self, root):
        self._root = root

    def local_server(self):
        # Crear servidor local que escucha por el puerto 8090
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind(('localHost', PORT))
        server_socket.listen(1)
        print("\tLocal server listening on port {PORT}")

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

        params = {'code': auth_code, 'grant_type': 'authorization_code', 'client_id': app_key, 'client_secret': app_secret, 'redirect_uri': redirect_uri}
        cabeceras={'User-Agent':'Python Client', 'Content-Type': 'application/x-www-form-urlencoded'}

        uri='https://api.dropboxapi.com/oauth2/token'
        respuesta = requests.post( uri, headers=cabeceras,data=params)
        print ("\t" + str(respuesta.status_code))
        json_respuesta = json.loads(respuesta.content)
        access_token = json_respuesta['access_token']
        print ("\tAccess_Token:"+ access_token)

        self._access_token = access_token

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

    def list_folder(self, msg_listbox):
        print("/list_folder")
        print(f"a: {self._access_token} p:{self._path}")

        uri = 'https://api.dropboxapi.com/2/files/list_folder'
        datos = {'path': self._path}
        datos_encoded = json.dumps(datos)

        cabeceras = {
            'Host': 'api.dropboxapi.com',
            'Authorization': f"Bearer {self._access_token}",
            'Content-Type': 'application/json'
            }
        respuesta = requests.post(uri, headers=cabeceras, data=datos_encoded,allow_redirects=False)
        status = respuesta.status_code
        print ("\tStatus: " + str(status))

        contenido = respuesta.text
        try:
            contenido_json = json.loads(contenido)
            self._files = helper.update_listbox2(msg_listbox, self._path, contenido_json)
        except:
            print("Path invalido")
            exit(1)

    def transfer_file(self, file_path, file_data):
        print("/upload")
        url = "https://content.dropboxapi.com/2/files/upload"
        
        print("El path del arhcivo a subir es:"+file_path)
        file_path=file_path.replace(" ","_")

        headers = {
            "Authorization": "Bearer "+self._access_token,
            "Content-Type": "application/octet-stream",
            "Dropbox-API-Arg": "{\"path\":\"" + file_path + "\"}"
            }

        data = file_data

        r = requests.post(url, headers=headers, data=data)
        print(r.status_code)

    def delete_file(self, file_path):
        print("/delete_file")
        url = "https://api.dropboxapi.com/2/files/delete_v2"

        headers = {
            "Authorization": "Bearer " +  self._access_token,
            "Content-Type": "application/json"
         }
        data = {"path": file_path}

        r = requests.post(url, headers=headers, data=json.dumps(data))

    def create_folder(self, path):
        print("/create_folder")
        url = "https://api.dropboxapi.com/2/files/create_folder_v2"

        headers = {
            "Authorization": "Bearer " + _access_token,
            "Content-Type": "application/json"
            }
        data = {"path": path}

        r = requests.post(url, headers=headers, data=json.dumps(data))
       
