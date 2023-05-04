# Alan Garcia Justel
# Sistemas Web Grupo G1
# 27/03/2023
# Lab2 - Descargar pdfs 
#
# Programa que accede con las credenciales del usuario a eGela
# y descarga los pdfs de la asignatura Sistemas Web en una carpeta
#

import os
import sys
import getpass
import requests
import urllib.parse
from bs4 import BeautifulSoup
import csv

# Variables globales del programa
ASIGNATURA = "Sistemas Web"
DIR_DESCARGA = os.path.join(os.getcwd(), "pdfs")
PATH_CSV = os.path.join(os.getcwd(), "entregas.csv")

HOST = "egela.ehu.eus"

# Funciones y métodos auxiliares
def usage():
    print(f"- python descargar_pdfs.py <id_usuario_eGela> \"<nombre_apellido>\"")
    print(f"\t id_usuario_eGela: Código empleado para acceder a eGela.")
    print(f"\t nombre_apellido:  Nombre y apellido que aparecen en eGela. Atención a los signos de puntuación.")
    print(f"-Valores por defecto:")
    print(f"HOST:           {HOST}")
    print(f"ASIGNATURA:     {ASIGNATURA}")
    print(f"-Ejemplo: python3 main.py 1027093 \"Alan García\"")

def crear_directorio_descarga():
    # PRE: ---
    # POST: Crea el directorio de descarga. Si ya existe, borra su contenido
    
    # Si no existe, creamos el directorio
    if not os.path.isdir(DIR_DESCARGA):
        os.mkdir(DIR_DESCARGA)

    # Borramos el contenido del directorio
    for filename in os.listdir(DIR_DESCARGA):
        file_path = os.path.join(DIR_DESCARGA, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def guardar_pdf(nombre, data):
    ruta = os.path.join(os.getcwd(), DIR_DESCARGA, nombre)

    fichero = open(ruta, 'wb')
    fichero.write(data)
    fichero.close()

def login_egela(username, nomb_ape, password):
    # PRE: HOST, USERNAME, PASSWORD y ASIGNATURA de eGela (variables globales)
    # POST: se devuelve la cookie del usuario loggeado correctamente y la url de Sistemas Web
    
    # Peticion 1 GET HOST/ -> 303 Redirect a HOST/login/index.php y Cookie
    print(f"[LOGIN] Peticion 1 -> GET https://{HOST}/")
    res = requests.get("https://" + HOST + "/", allow_redirects=False)
    print(f"{res.status_code} {res.reason}")

    if (res.status_code < 300 or res.status_code >= 400):
        print("[LOGIN] ERROR: Error en el codigo de respuesta de la petición 1. Se esperaba un 303 Redirect")
        exit(1)

    url_redirect = res.headers['Location']
    cookie = res.headers['Set-Cookie'].split(";")[0]
    print(f"url_redirect: {url_redirect}")
    print(f"cookie: {cookie}")

    # Peticion 2 GET HOST/login/index.php-> Obtenemos el formulario y extraemos el logintoken
    print(f"\n[LOGIN] Peticion 2 -> GET {url_redirect}")
    headers = {'Cookie': cookie}
    
    res = requests.get(url_redirect, headers=headers, allow_redirects=False)
    print(f"{res.status_code} {res.reason}")

    if (res.status_code < 200 or res.status_code >= 300):
        print("[LOGIN] ERROR: Error en el codigo de respuesta de la petición 2. Se esperaba un 200 OK")
        exit(1)

    logintoken = str(res.content).split("name=\"logintoken\"")[1].split("\"")[1]
    print(f"logintoken: {logintoken}")

    # Peticion 3 POST HOST/login/index.php -> 303 Redirect y nueva Cookie
    print(f"\n[LOGIN] Peticion 3 -> POST {url_redirect}")
    headers = {'Cookie': cookie, "Content-Type": "application/x-www-form-urlencoded"}
    body = {"logintoken" : logintoken, "username": username, "password": password}
    body = urllib.parse.urlencode(body)
    print(f"[LOGIN] Body: {body}")
    
    res = requests.post(url_redirect, data=body, headers=headers, allow_redirects=False)
    print(f"{res.status_code} {res.reason}")

    if (res.status_code < 300 or res.status_code >= 400):
        print("[LOGIN] ERROR: Error en el codigo de respuesta de la petición 3. Username o password no validas")
        exit(1)

    url_redirect = res.headers['Location']

    if 'Set-Cookie' not in res.headers:
        print("[LOGIN] ERROR: No se encuentra la cabecera Set-Cookie. Username o password no validas")
        exit(1)

    cookie = res.headers['Set-Cookie'].split(";")[0]
    print(f"url_redirect: {url_redirect}")
    print(f"cookie: {cookie}")

    # Peticion 4 GET HOST/login/index.php?testsession=xxxx -> 303 Redirect a https://egela.ehu.eus/
    print(f"\n[LOGIN] Peticion 4 -> GET {url_redirect}")
    headers = {'Cookie': cookie}

    res = requests.get(url_redirect, headers=headers, allow_redirects=False)
    print(f"{res.status_code} {res.reason}")

    if (res.status_code < 300 or res.status_code >= 400):
        print("[LOGIN] ERROR: Error en el codigo de respuesta de la petición 4. Se esperaba un redirect a https://egela.ehu.eus/")
        exit(1)
    
    url_redirect = res.headers['Location']
    print(f"url_redirect: {url_redirect}")

    # Peticion 5 GET HOST/ -> Pagina principal de eGela loggeados
    print(f"\n[LOGIN] Peticion 5 -> GET {url_redirect}")
    headers = {'Cookie': cookie}

    res = requests.get(url_redirect, headers=headers, allow_redirects=False)
    print(f"{res.status_code} {res.reason}")

    if (res.status_code < 200 or res.status_code >= 300):
        print("[LOGIN] ERROR: Error en el codigo de respuesta de la petición 5. Se esperaba un 200 OK -> loggeados en la pagina principal de eGela")
        exit(1)

    if res.content.decode('utf-8').find(nomb_ape) == -1:
        print(f"[LOGIN] ERROR: No se encontró la cadena {nomb_ape} en la pagina principal de eGela")
        exit(1)
    print(f"[LOGIN] Usuario {username} {nomb_ape} loggeado correctamente en eGela")

    # Parseamos el html y buscamos la url de Sistemas Web
    document = BeautifulSoup(res.content, 'html.parser')
    cursos = document.find_all('h3', {"class": "coursename"})
    url_sw = ""
    for c in cursos:
        if c.getText() == ASIGNATURA:
            a = c.find('a')
            url_sw = a['href']

    print(f"[LOGIN] url {ASIGNATURA}: {url_sw}")
    return cookie, url_sw

def obtener_urls_pdfs(cookie, url_sw):
    # PRE: cookie del usuario loggeado y url de la asignatura
    # POST: devolvemos las urls de los pdfs de Sistemas Web
    print(f"[URL_SW] GET a {url_sw}")
    headers = {'Cookie': cookie}
    res = requests.get(url_sw, headers=headers, allow_redirects=False)
    if (res.status_code < 200 or res.status_code >= 300):
        print("[URL_SW] ERROR: No se pudo obtener la pagina de la asignatura de eGela")
        exit(1)
    
    body = res.content.decode("utf-8")
    activity_instances = body.split('<div class=\"activityinstance\">')[1:]
    
    urls_redirects = [] # urls que redireccionan a las urls de los pdfs
    for a in activity_instances:
        if(a.find("pdf") != -1):
            # Se trata de un pdf -> los logos que aparecen al lado de los archivhos tienen la cadena "pdf"
            # Obtenemos el href del hipervinculo <a></a>
            direc = a.split('href=\"')[1].split('\"')[0]
            urls_redirects.append(direc)
    
    urls = [] # urls de los pdfs
    for u in urls_redirects:
        print(f"[URL_SW] Obteniendo url pdf de {u}")
        res = requests.get(u, headers=headers, allow_redirects=False)
        if (res.status_code < 300 or res.status_code >= 400):
            print(f"[URL_SW] ERROR: No se pudo obtener la url del pdf: {u}")
        urls.append(res.headers['Location'])

    return urls

def obtener_urls_entregas(cookie, url_sw):
    # PRE: cookie del usuario loggeado y url de la asignatura
    # POST: devolvemos las urls de las entregas de Sistemas Web
    print(f"[URL_SW] GET a {url_sw}")
    headers = {'Cookie': cookie}
    res = requests.get(url_sw, headers=headers, allow_redirects=False)
    if (res.status_code < 200 or res.status_code >= 300):
        print("[URL_SW] ERROR: No se pudo obtener la pagina de la asignatura de eGela")
        exit(1)
    
    document = BeautifulSoup(res.content, 'html.parser')
    lista_entregas = document.find_all('img', {'src': 'https://egela.ehu.eus/theme/image.php/ehu/assign/1678718742/icon'})
    print(lista_entregas)

    urls = []
    for i in lista_entregas:
        attrs = i.parent.attrs
        if 'href' not in attrs.keys():
            continue

        url = attrs['href']
        urls.append(url)
        print(f"[URL_SW] Obteniendo url entrega -> {url}")

    return urls

def obtener_lista_entregas(cookie, urls_entregas):
    # PRE: cookie del usuario logeado y urls de los pdfs a descargar
    # POST: lista con la información de cada entrega [{'nombre': "nombre", 'url': "url", 'fecha_entrega': "fecha"}, ...]
    entregas = []
    for url in urls_entregas:
        print(f"[ENTREGA] GET a {url}")
        headers = {'Cookie': cookie}
        res = requests.get(url, headers=headers, allow_redirects=False)
        if (res.status_code < 200 or res.status_code >= 300):
            print("[ENTREGA] ERROR: No se pudo obtener la pagina de la asignatura de eGela")
            exit(1)

        document = BeautifulSoup(res.content, 'html.parser')
        nombre = document.find('h2').get_text()
        
        trs = document.find_all('tr')
        fecha_entrega = trs[2].find('td', {'class': "cell c1 lastcol"}).get_text()
        entregas.append({'nombre': nombre, 'url': url, 'fecha_entrega': fecha_entrega})

    return entregas

def guardar_entregas_csv(lista_entregas):
    # PRE: lista de entregas
    # POST: se guardan las entregas en un csv
    keys = lista_entregas[0].keys()
    with open(PATH_CSV, 'w') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(lista_entregas)

def descargar_pdfs_egela(cookie, urls):
    # PRE: cookie del usuario logeado y urls de los pdfs a descargar
    # POST: se descargan los pdfs y se guardan en la carpeta definida
    headers = {'Cookie': cookie}
    for url in urls:
        print(f"[DESCARGA] Descargando {url}")
        res = requests.get(url, headers=headers, allow_redirects=True)
        if (res.status_code < 200 or res.status_code >= 300):
            print(f"[DESCARGA] ERROR: No se pudo acceder al recurso: {url}")
        

        nombre = urllib.parse.unquote(url.split("/")[-1])
        nombre = nombre.replace(" ", "_")

        guardar_pdf(nombre, res.content)
        
    return

# Entrada principal del programa
def main(args):
    # Recogiendo los datos del usuario
    username = args[1]
    nomb_ape = args[2]
    print(f"---- Tomando datos del usuario {username} {nomb_ape}")
    password = getpass.getpass()

    # Creamos el directorio de descarga
    print(f"\n---- Creando y limpiando directorio de descarga: ({DIR_DESCARGA})")
    crear_directorio_descarga()
    
    # Nos loggeamos en eGela y obtenemos la url de la pagina de Sistemas Web
    print(f"\n---- Accediendo a eGela -> obtenemos cookie para {username} y url de {ASIGNATURA}")
    cookie, url_sw = login_egela(username, nomb_ape, password)
    
    # Obtenemos las urls de los pdfs de la Asignatura
    print(f"\n---- Obteniendo urls de pdfs presentes en {url_sw}")
    urls_pdfs = obtener_urls_pdfs(cookie, url_sw)
    
    # Obtenemos las urls de las entregas de la Asignatura
    print(f"\n---- Obteniendo urls de entregas presentes en {url_sw}")
    urls_entregas = obtener_urls_entregas(cookie, url_sw)

    # Obtenemos la información de cada entrega y las guardamos en un archivo csv
    print(f"\n---- Obteniendo informacion de las entregas")
    lista_entregas = obtener_lista_entregas(cookie, urls_entregas)
    print(f"\n---- Guardando entregas")
    guardar_entregas_csv(lista_entregas)

    # Descargamos los contenidos de las urls en la carpeta definida
    print(f"\n---- Descargando y guardando pdfs")
    descargar_pdfs_egela(cookie, urls_pdfs)


if __name__ == "__main__":
    # Comprobamos si los argumentos son correctos
    if len(sys.argv) != 3:
        usage()
        exit(1)
    
    # Ejecutamos el programa principal
    main(sys.argv)