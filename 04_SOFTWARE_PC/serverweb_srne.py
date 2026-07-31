#!/usr/bin/env python3
"""
============================================================================
Servidor web local para ADA-FV — SRNE HF2430U80-H via ESP32-C3
============================================================================

PROPOSITO:
  Leer el JSON del ESP32-C3 por USB Serial y servirlo en un navegador web
  con una pagina sencilla de fondo blanco y texto grande.

ARQUITECTURA:
  ESP32-C3 --(JSON USB Serial)--> servidor (localhost:8080) --> navegador

USO:
  python3 serverweb_srne.py                  # auto-detecta el puerto
  python3 serverweb_srne.py /dev/ttyUSB0     # puerto explicito

ABRIR EN EL NAVEGADOR:
  http://localhost:8080

SALIR:
  Ctrl+C
============================================================================
"""

import json         # Parsear el JSON del ESP32
import threading    # Hilo lector en segundo plano
import time         # Control del ciclo de actualizacion
import argparse     # Opciones de linea de comandos
from http.server import BaseHTTPRequestHandler, HTTPServer  # Servidor HTTP
import serial       # Comunicacion serial con el ESP32-C3
import serial.tools.list_ports  # Deteccion automatica de puertos

# Configuracion del servidor HTTP
HOST = "127.0.0.1"      # Solo acceso local (no exponer a la red)
PORT = 8080             # Puerto del servidor web
TAMANIO_TEXTO = "5vw"   # Tamano de letra de la pagina web

# Estado global compartido entre el hilo lector y el servidor
samples = {}            # Ultima muestra de datos recibida del ESP32
lock = threading.Lock() # Protege el acceso a "samples" entre hilos

# ============================================================================
# HILO LECTOR DEL ESP32 (corre en segundo plano)
# ============================================================================
def hilo_lector(port):
    """Lee el JSON del ESP32-C3 y actualiza la variable global 'samples'.

    Parametros:
        port : ruta del puerto serial (ej: /dev/ttyUSB0)
    Este hilo corre hasta que el programa se detenga.
    """
    global samples
    ser = serial.Serial(port, 115200, timeout=2)   # Conectar al ESP32
    print(f"Leyendo ESP32 en {port} @115200 baud...")

    while True:
        try:
            line = ser.readline().decode(errors="replace").strip()
            if not line:
                continue
            data = json.loads(line)                # Parsear JSON
            if data.get("t") == "data":            # Solo tramas de datos
                with lock:                         # Proteger acceso
                    samples = data.get("samples", {})
        except serial.SerialException:
            time.sleep(1)                          # Reconectar mas tarde
            try:
                ser = serial.Serial(port, 115200, timeout=2)
            except:
                pass
        except:
            pass                                   # Ignorar errores menores

# ============================================================================
# MANEJADOR DE PETICIONES HTTP
# ============================================================================
class Manejador(BaseHTTPRequestHandler):
    """Atiende las peticiones del navegador.

    - GET /      -> pagina HTML con los datos en vivo
    - GET /api   -> respuesta JSON para que la pagina la consulte
    """

    def log_message(self, *a):
        pass  # Silenciar el log de peticiones de la consola

    def do_GET(self):
        # --- Endpoint /api: devuelve los ultimos datos como JSON ---
        if self.path == "/api":
            with lock:
                payload = samples   # Copia segura bajo el lock
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # --- Pagina HTML principal (cualquier otra ruta) ---
        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>ADA-FV - SRNE HF2430U80-H</title>
<style>
  body {{ background: #fff; font-family: monospace; text-align: center; }}
  h1 {{ font-size: {TAMANIO_TEXTO}; }}
  div {{ font-size: {TAMANIO_TEXTO}; }}
</style>
</head>
<body>
<h1>ADA-FV - SRNE HF2430U80-H</h1>
<div id="datos">Esperando datos...</div>
<script>
  // Consulta el endpoint /api cada 2 segundos y actualiza la pagina
  async function refresh() {{
    const r = await fetch('/api');
    const d = await r.json();
    const c = (k, u) => d[k] !== undefined ? d[k] + ' ' + u : '---';
    document.getElementById('datos').innerHTML =
      'SOC: ' + c('SOC','%') + ' &nbsp; Vbat: ' + c('Vbat','V') +
      ' &nbsp; PV: ' + c('PV_P','W') + ' &nbsp; Carga: ' + c('Load_P','W') +
      '<br><br>' + new Date().toLocaleTimeString();
  }}
  refresh();
  setInterval(refresh, 2000);   // Actualizar cada 2 segundos
</script>
</body>
</html>"""
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

# ============================================================================
# DETECCION AUTOMATICA DE PUERTO SERIAL
# ============================================================================
def detect_port():
    """Busca un puerto serial disponible (ESP32-C3 conectado por USB)."""
    for p in serial.tools.list_ports.comports():
        if any(kw in p.description.lower() for kw in ["usb","serial","ch340","cp210","ftdi","uart"]):
            return p.device
    for p in serial.tools.list_ports.comports():
        return p.device
    return None

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================
def main():
    """Punto de entrada: arranca el hilo lector y el servidor web."""
    ap = argparse.ArgumentParser(description="Servidor web de ADA-FV")
    ap.add_argument("port_serial", nargs="?", default=None,
                    help="Puerto serial del ESP32 (auto-detecta si se omite)")
    args = ap.parse_args()

    # Determinar el puerto serial
    port = args.port_serial or detect_port()
    if not port:
        print("ERROR: No se detecto puerto serial.")
        return

    # Arrancar el hilo lector en segundo plano (daemon: muere con el main)
    t = threading.Thread(target=hilo_lector, args=(port,), daemon=True)
    t.start()

    # Arrancar el servidor web
    print(f"Servidor web en http://{HOST}:{PORT}")
    try:
        HTTPServer((HOST, PORT), Manejador).serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")

if __name__ == "__main__":
    main()
