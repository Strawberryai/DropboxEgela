# -*- coding: UTF-8 -*-
import requests
import urllib
from bs4 import BeautifulSoup
import time
import helper

HOST = "egela.ehu.eus"
ASIGNATURA = "Sistemas Web"

class eGela:
    _login = 0
    _cookie = ""
    _curso = ""
    _refs = []
    _root = None

    def __init__(self, root):
        self._root = root

    def check_credentials(self, username, password, event=None):
        popup, progress_var, progress_bar = helper.progress("check_credentials", "Logging into eGela...")
        progress = 0
        progress_var.set(progress)
        progress_bar.update()
        
        print("##### 1. PETICION #####")
        res = requests.get("https://" + HOST + "/", allow_redirects=False)
        print(f"{res.status_code} {res.reason}")

        if (res.status_code < 300 or res.status_code >= 400):
            print("[LOGIN] ERROR: Error en el codigo de respuesta de la petición 1. Se esperaba un 303 Redirect")
            return 1

        url_redirect = res.headers['Location']
        cookie = res.headers['Set-Cookie'].split(";")[0]
        print(f"url_redirect: {url_redirect}")
        print(f"cookie: {cookie}")
    
        progress = 10
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        print("##### 2. PETICION #####")
        headers = {'Cookie': cookie}
    
        res = requests.get(url_redirect, headers=headers, allow_redirects=False)
        print(f"{res.status_code} {res.reason}")
    
        if (res.status_code < 200 or res.status_code >= 300):
            print("[LOGIN] ERROR: Error en el codigo de respuesta de la petición 2. Se esperaba un 200 OK")
            return 1
    
        logintoken = str(res.content).split("name=\"logintoken\"")[1].split("\"")[1]
        print(f"logintoken: {logintoken}")

        progress = 25
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        print("\n##### 3. PETICION #####")
        headers = {'Cookie': cookie, "Content-Type": "application/x-www-form-urlencoded"}
        body = {"logintoken" : logintoken, "username": username, "password": password}
        body = urllib.parse.urlencode(body)
        print(f"[LOGIN] Body: {body}")

        res = requests.post(url_redirect, data=body, headers=headers, allow_redirects=False)
        print(f"{res.status_code} {res.reason}")

        if (res.status_code < 300 or res.status_code >= 400):
            print("[LOGIN] ERROR: Error en el codigo de respuesta de la petición 3. Username o password no validas")
            return 1

        url_redirect = res.headers['Location']

        if 'Set-Cookie' not in res.headers:
            print("[LOGIN] ERROR: No se encuentra la cabecera Set-Cookie. Username o password no validas")
            return 1

        cookie = res.headers['Set-Cookie'].split(";")[0]
        print(f"url_redirect: {url_redirect}")
        print(f"cookie: {cookie}")

        progress = 50
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        print("\n##### 4. PETICION #####")
        headers = {'Cookie': cookie}

        res = requests.get(url_redirect, headers=headers, allow_redirects=False)
        print(f"{res.status_code} {res.reason}")
    
        if (res.status_code < 300 or res.status_code >= 400):
            print("[LOGIN] ERROR: Error en el codigo de respuesta de la petición 4. Se esperaba un redirect a https://egela.ehu.eus/")
            exit(1)
        
        url_redirect = res.headers['Location']
        print(f"url_redirect: {url_redirect}")

        progress = 75
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        print("\n##### 5. PETICION #####")
        headers = {'Cookie': cookie}

        res = requests.get(url_redirect, headers=headers, allow_redirects=False)
        print(f"{res.status_code} {res.reason}")

        if (res.status_code < 200 or res.status_code >= 300):
            print("[LOGIN] ERROR: Error en el codigo de respuesta de la petición 5. Se esperaba un 200 OK -> loggeados en la pagina principal de eGela")
            return 1

        print(f"[LOGIN] Usuario {username} loggeado correctamente en eGela")

        # Parseamos el html y buscamos la url de Sistemas Web
        document = BeautifulSoup(res.content, 'html.parser')
        cursos = document.find_all('h3', {"class": "coursename"})
        url_sw = ""
        for c in cursos:
            if c.getText() == ASIGNATURA:
                a = c.find('a')
                url_sw = a['href']

        progress = 100
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)
        popup.destroy()
		

        # ACTUALIZAR VARIABLES
        self._login = 1
        self._cookie = cookie
        self._curso = url_sw
        
        self._root.destroy()
        
            

    def get_pdf_refs(self):
        popup, progress_var, progress_bar = helper.progress("get_pdf_refs", "Downloading PDF list...")
        progress = 0
        progress_var.set(progress)
        progress_bar.update()

        print("\n##### 4. PETICION (Página principal de la asignatura en eGela) #####")
        headers = {'Cookie': self._cookie}
        res = requests.get(self._curso, headers=headers, allow_redirects=False)
        if (res.status_code < 200 or res.status_code >= 300):
            print("[URL_SW] ERROR: No se pudo obtener la pagina de la asignatura de eGela")
            return
        
        body = res.content.decode("utf-8")
        activity_instances = body.split('<div class=\"activityinstance\">')[1:]
        urls_redirects = [] # urls que redireccionan a las urls de los pdfs
        for a in activity_instances:
            if(a.find("pdf") != -1):
                # Se trata de un pdf -> los logos que aparecen al lado de los archivhos tienen la cadena "pdf"
                # Obtenemos el href del hipervinculo <a></a>
                direc = a.split('href=\"')[1].split('\"')[0]
                urls_redirects.append(direc)

        progress = 10
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        print("\n##### Analisis del HTML... #####")
        # INICIALIZA Y ACTUALIZAR BARRA DE PROGRESO
        # POR CADA PDF ANIADIDO EN self._refs
        progress_step = float(90.0 / len(urls_redirects))

        for u in urls_redirects:
            res = requests.get(u, headers=headers, allow_redirects=False)
            if (res.status_code < 300 or res.status_code >= 400):
                print(f"[URL_SW] ERROR: No se pudo obtener la url del pdf: {u}")
            
            url = res.headers['Location']
            nombre = urllib.parse.unquote(url.split("/")[-1])
            pdf = {
                "pdf_name": nombre,
                "pdf_url": url
                }

            self._refs.append(pdf)
            
            progress += progress_step
            progress_var.set(progress)
            progress_bar.update()
            time.sleep(0.01)
        
        popup.destroy()

        return self._refs

    def get_pdf(self, selection):

        print("\t##### descargando  PDF... #####")
        pdf_content = requests.get(self._refs[selection]['pdf_url'], headers={'Cookie': self._cookie}, allow_redirects=True).content

        return self._refs[selection]['pdf_name'], pdf_content
