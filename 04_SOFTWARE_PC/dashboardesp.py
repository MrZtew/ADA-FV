#!/usr/bin/env python3
"""
============================================================================
Dashboard en terminal (curses) para ADA-FV — SRNE HF2430U80-H
============================================================================

PROPOSITO:
  Leer el JSON que envia el ESP32-C3 por USB Serial y mostrarlo en la
  terminal en tiempo real, organizado por grupos (panel, bateria, red, etc).

ARQUITECTURA:
  ESP32-C3 --(JSON por USB Serial)--> este script --> terminal curses

USO:
  python3 dashboardesp.py                  # auto-detecta el puerto
  python3 dashboardesp.py /dev/ttyUSB0     # puerto explicito

TECLAS:
  Q  -> salir del dashboard

NOTA:
  Este script NO habla Modbus. Solo lee el JSON que el ESP32-C3 ya
  proceso y envio escalado. Para hablar Modbus directo desde PC use
  dashboard_srne.py o test_modbus_srne.py.
============================================================================
"""

import sys          # Argumentos de linea de comandos
import time         # Pausas y temporizacion
import json         # Parsear el JSON que llega por serial
import curses       # Interfaz de terminal en tiempo real
import serial       # Comunicacion serial con el ESP32-C3
import serial.tools.list_ports  # Deteccion automatica de puertos
from datetime import datetime   # Marca de tiempo para la cabecera

# ============================================================================
# TABLA DE CAMPOS A MOSTRAR
# ============================================================================
# Cada entrada: (clave_json, nombre_visible, unidad, factor, signed, decimales)
# El factor SIEMPRE es 1 porque el ESP32-C3 ya escala los valores.
# El "signed" no se aplica: el ESP32 ya lo interpreto.
FIELDS = [
    ("SOC",       "SOC",        "%",     1,   False, 0),  # Estado de carga [%]
    ("Vbat",      "Vbat",       "V",     1,   False, 1),  # Voltaje bateria [V]
    ("Ibat",      "Ibat",       "A",     1,   True,  1),  # Corriente bateria [A]
    ("PV1_V",     "PV1 V",      "V",     1,   False, 1),  # Voltaje panel [V]
    ("PV1_I",     "PV1 I",      "A",     1,   False, 1),  # Corriente panel [A]
    ("PV1_P",     "PV1 P",      "W",     1,   False, 0),  # Potencia panel [W]
    ("PV_P",      "PV total P", "W",     1,   False, 0),  # Potencia PV total [W]
    ("Carga",     "Carga",      "",      1,   False, 0),  # Estado de carga (codigo)
    ("Chg_P",     "Charge P",   "W",     1,   False, 0),  # Potencia de carga [W]
    ("Estado",    "Estado",     "",      1,   False, 0),  # Estado de maquina
    ("Grid_V",    "Grid V",     "V",     1,   False, 1),  # Voltaje de red [V]
    ("Grid_I",    "Grid I",     "A",     1,   False, 1),  # Corriente de red [A]
    ("Grid_Hz",   "Grid Hz",    "Hz",    1,   False, 2),  # Frecuencia de red [Hz]
    ("Inv_V",     "Inv V",      "V",     1,   False, 1),  # Voltaje inversor [V]
    ("Inv_I",     "Inv I",      "A",     1,   False, 1),  # Corriente inversor [A]
    ("Inv_Hz",    "Inv Hz",     "Hz",    1,   False, 2),  # Frecuencia inversor [Hz]
    ("Load_I",    "Load I",     "A",     1,   False, 1),  # Corriente de carga [A]
    ("Load_P",    "Load P",     "W",     1,   False, 0),  # Potencia activa [W]
    ("Load_VA",   "Load VA",    "VA",    1,   False, 0),  # Potencia aparente [VA]
    ("T_DCDC",    "T DC-DC",    "C",     1,   True,  1),  # Temp. DC-DC [C]
    ("T_DCAC",    "T DC-AC",    "C",     1,   True,  1),  # Temp. DC-AC [C]
    ("T_Trafo",   "T Trafo",    "C",     1,   True,  1),  # Temp. trafo [C]
    ("T_Amb",     "T Amb",      "C",     1,   True,  1),  # Temp. ambiente [C]
    ("PV_hoy",    "PV hoy",     "kWh",   1,   False, 1),  # Energia PV de hoy [kWh]
    ("Load_hoy",  "Load hoy",   "kWh",   1,   False, 1),  # Energia consumida hoy [kWh]
]

# Diccionarios de acceso rapido por clave JSON
KEYNAME = {f[0]: f[1] for f in FIELDS}   # clave -> nombre visible
KEYUNIT = {f[0]: f[2] for f in FIELDS}   # clave -> unidad
KEYDEC  = {f[0]: f[5] for f in FIELDS}   # clave -> cantidad de decimales

# ============================================================================
# TABLAS DE DECODIFICACION DE CODIGOS
# ============================================================================
# Estado de la maquina (registro 0x0210 / campo "Estado")
ESTADOS = {0:"Power-on", 1:"Standby", 2:"Init", 3:"SoftStart",
           4:"AC op", 5:"Inverter op", 6:"Inv->AC", 7:"AC->Inv",
           8:"Bat activ", 9:"Manual off", 10:"Fault"}
# Estado de carga (registro 0x010B / campo "Carga")
CARGAS = {0:"Off", 1:"Quick", 2:"ConstV", 4:"Float", 6:"Li activ", 8:"Full"}

# ============================================================================
# FORMATEO DE UNA LINEA DEL DASHBOARD
# ============================================================================
def formatear(key, raw):
    """Convierte el valor crudo del JSON en texto listo para mostrar.

    Parametros:
        key : clave del campo en el JSON (ej: "Vbat")
        raw : valor numerico recibido (o None si el ESP32 no respondio)
    Retorna:
        string con el texto formateado, ej: "      Vbat: 27.9 V"
    """
    if raw is None:
        # El ESP32 no obtuvo respuesta del inversor para este campo
        return f"{KEYNAME[key]:>10s}: ---"

    dec = KEYDEC.get(key, 1)            # Decimales para este campo
    v = float(raw)                      # Valor ya escalado por el ESP32
    fmt = f"{KEYNAME[key]:>10s}: {v:.{dec}f} {KEYUNIT.get(key,'')}"

    # Anadir descripcion textual para los campos de codigo
    if key == "Estado" and raw in ESTADOS:
        fmt += f"  ({ESTADOS[int(raw)]})"
    if key == "Carga" and raw in CARGAS:
        fmt += f"  ({CARGAS[int(raw)]})"
    if key == "Ibat" and raw is not None:
        # Convencion SRNE: positivo = descarga, negativo = carga
        sentido = "Desc" if float(raw) > 0 else "Carga"
        fmt += f" ({sentido})"
    return fmt

# ============================================================================
# DETECCION AUTOMATICA DE PUERTO SERIAL
# ============================================================================
def detect_port():
    """Busca un puerto serial disponible (ESP32-C3 conectado por USB)."""
    # Primera pasada: preferir puertos con nombre sugerente
    for p in serial.tools.list_ports.comports():
        if any(kw in p.description.lower() for kw in ["usb","serial","ch340","cp210","ftdi","uart"]):
            return p.device
    # Segunda pasada: usar el primer puerto que exista
    for p in serial.tools.list_ports.comports():
        return p.device
    return None                        # No se encontro ningun puerto

# ============================================================================
# BUCLE PRINCIPAL DEL DASHBOARD (curses)
# ============================================================================
def dashboard(stdscr, port):
    """Dibuja el dashboard en tiempo real usando curses.

    Parametros:
        stdscr : objeto de pantalla que provee curses.wrapper
        port   : ruta del puerto serial (ej: /dev/ttyUSB0)
    """
    # --- Configuracion de curses ---
    curses.curs_set(0)                  # Ocultar el cursor
    curses.use_default_colors()         # Usar colores por defecto del terminal
    stdscr.nodelay(1)                   # getch() sin bloqueo
    stdscr.timeout(2000)                # Timeout de espera de teclado (2s)

    # --- Abrir el puerto serial hacia el ESP32-C3 ---
    try:
        ser = serial.Serial(port, 115200, timeout=5)  # 115200 baud
        ser.reset_input_buffer()        # Limpiar datos viejos del buffer
    except Exception as e:
        stdscr.addstr(0, 0, f"ERROR: {e}")
        stdscr.refresh()
        time.sleep(3)
        return

    samples = {}                        # Ultimo muestreo recibido (dict)
    blink = False                       # Estado del indicador [X] / [ ]

    while True:
        stdscr.erase()                  # Limpiar pantalla
        h, w = stdscr.getmaxyx()        # Tamano actual de la terminal

        # --- Leer lineas JSON del ESP32 (hasta 5 por refresco) ---
        new_data = False
        for _ in range(5):
            try:
                line = ser.readline().decode(errors="replace").strip()
                if not line: continue
                data = json.loads(line)         # Parsear el JSON
                if data.get("t") == "data":     # Solo tramas de datos
                    samples = data.get("samples", {})
                    new_data = True
            except: pass                        # Ignorar lineas corruptas

        # Parpadear el indicador si llego un dato nuevo
        if new_data:
            blink = not blink

        # Marca de tiempo de la cabecera
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # --- Cabecera ---
        F = curses.A_BOLD               # Atributo negrita
        led = "[X]" if blink else "[ ]" # Indicador de datos recibidos
        stdscr.addstr(0, 0, "=" * min(w-1, 70), F)
        stdscr.addstr(1, 0, f"  {led}  ADA-FV - SRNE HF2430U80-H    {now}", F)
        stdscr.addstr(2, 0, f"  Puerto: {port}  |  via ESP32-C3", F)
        stdscr.addstr(3, 0, "=" * min(w-1, 70), F)

        # --- Definicion de los grupos de datos a mostrar ---
        grupos = [
            ("PANEL SOLAR",   ["PV1_V","PV1_I","PV1_P","PV_P"]),
            ("BATERIA",       ["SOC","Vbat","Ibat","Carga"]),
            ("CARGA AC",      ["Inv_V","Inv_I","Load_I","Load_P","Load_VA"]),
            ("RED",           ["Grid_V","Grid_I","Grid_Hz"]),
            ("TEMPERATURAS",  ["T_DCDC","T_DCAC","T_Trafo","T_Amb"]),
            ("ESTADO",        ["Estado"]),
            ("ENERGIA HOY",   ["PV_hoy","Load_hoy"]),
        ]

        # --- Dibujar cada grupo y sus campos ---
        line = 5                        # Fila inicial (despues de la cabecera)
        for titulo, keys in grupos:
            if line >= h-2: break       # No salirse de la pantalla
            stdscr.addstr(line, 0, f"-- {titulo} --", F)
            line += 1
            for key in keys:
                if line >= h-2: break
                txt = formatear(key, samples.get(key))
                stdscr.addstr(line, 0, txt)
                line += 1
            line += 1                   # Fila en blanco entre grupos

        # --- Pie de pagina ---
        if line < h-1:
            stdscr.addstr(line, 0, "=" * min(w-1, 70))
            stdscr.addstr(line+1, 0, "  Q=salir  |  actualiza cada ~500ms")

        stdscr.refresh()                # Volcar cambios a la terminal

        # --- Esperar tecla Q para salir (20 x 100ms = 2s) ---
        for _ in range(20):
            k = stdscr.getch()
            if k in (ord('q'), ord('Q')):
                ser.close()             # Cerrar puerto serial
                return
            time.sleep(0.1)

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================
def main():
    """Punto de entrada: detecta el puerto y lanza el dashboard curses."""
    port = sys.argv[1] if len(sys.argv) > 1 else detect_port()
    if not port:
        print("ERROR: No se detecto puerto.")
        sys.exit(1)
    # curses.wrapper se encarga de inicializar/restaurar la terminal
    curses.wrapper(dashboard, port)

if __name__ == "__main__":
    main()
