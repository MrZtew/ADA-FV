#!/usr/bin/env python3
"""
============================================================================
Lector de datos de ADA-FV — SRNE HF2430U80-H via ESP32-C3
============================================================================

PROPOSITO:
  Leer el JSON que envia el ESP32-C3 por USB Serial, mostrar las muestras
  en consola y opcionalmente guardarlas en un archivo CSV o log.

ARQUITECTURA:
  ESP32-C3 --(JSON por USB Serial)--> este script

MODOS DE USO:
  python3 reader_srne.py                    # Ver datos en consola
  python3 reader_srne.py --csv datos.csv    # Ver en consola + guardar CSV
  python3 reader_srne.py --log monitor.log  # Ver en consola + guardar log
  python3 reader_srne.py --port /dev/ttyUSB0 --seconds 10
  python3 reader_srne.py --count 50         # Leer solo 50 muestras

SALIR:
  Ctrl+C
============================================================================
"""

import sys          # Salida del programa
import time         # Control del tiempo de muestreo
import json         # Parsear el JSON del ESP32
import argparse     # Opciones de linea de comandos
import csv          # Escritura de archivos CSV
from datetime import datetime   # Marca de tiempo de cada muestra
import serial       # Comunicacion serial con el ESP32-C3
import serial.tools.list_ports  # Deteccion automatica de puertos

# ============================================================================
# DETECCION AUTOMATICA DE PUERTO SERIAL
# ============================================================================
def detect_port():
    """Busca un puerto serial disponible (ESP32-C3 conectado por USB).

    Retorna la ruta del primer puerto con nombre sugerente, o el primer
    puerto disponible, o None si no hay ninguno.
    """
    for p in serial.tools.list_ports.comports():
        if any(kw in p.description.lower() for kw in ["usb","serial","ch340","cp210","ftdi","uart"]):
            return p.device          # Puerto con nombre claro (ej: USB)
    for p in serial.tools.list_ports.comports():
        return p.device              # Cualquier puerto disponible
    return None                      # No hay puertos

# ============================================================================
# PROCESAMIENTO DE CADA MUESTRA
# ============================================================================
def procesar(data):
    """Muestra una trama de datos del ESP32 en consola.

    Parametros:
        data : dict con la trama JSON ya parseada.
               Ejemplo: {"t":"data","ms":1234,"samples":{"Vbat":27.9, ...}}
    """
    # Solo procesar tramas de datos (el ESP32 tambien envia otros tipos)
    if data.get("t") != "data":
        return

    samples = data.get("samples", {})          # Dict con los valores
    ts = datetime.now().strftime("%H:%M:%S")   # Hora local de la PC

    # Imprimir todos los campos que llegaron, uno por linea
    for k, v in samples.items():
        print(f"[{ts}] {k:>10s} = {v}")

    # Linea separadora + numero de muestras en esta trama
    n = len(samples)
    print(f"[{ts}] --- {n} campos ---\n")

# ============================================================================
# GUARDAR MUESTRAS EN ARCHIVO CSV
# ============================================================================
def guardar_csv(csvw, data):
    """Escribe una trama de datos como fila en un archivo CSV.

    Parametros:
        csvw : objeto csv.writer ya creado
        data : dict con la trama JSON del ESP32
    """
    if data.get("t") != "data":
        return
    samples = data.get("samples", {})
    fila = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]  # Marca de tiempo
    fila.extend(samples.get(k) for k in sorted(samples))     # Valores ordenados
    csvw.writerow(fila)                                     # Escribir fila

# ============================================================================
# LECTURA PRINCIPAL DESDE EL PUERTO SERIAL
# ============================================================================
def loop_lectura(port, csvw=None, flog=None, seconds=0, count=0):
    """Lee el flujo JSON del ESP32 hasta cumplir la condicion de salida.

    Parametros:
        port    : ruta del puerto serial
        csvw    : csv.writer opcional para guardar CSV
        flog    : archivo abierto opcional para log en texto
        seconds : duracion maxima en segundos (0 = sin limite)
        count   : cantidad maxima de muestras (0 = sin limite)
    """
    muestras = 0                        # Contador de muestras procesadas
    inicio = time.time()                # Momento de arranque

    with serial.Serial(port, 115200, timeout=5) as ser:
        print(f"Conectado a {port} @115200 baud. Ctrl+C para salir.\n")

        while True:
            # Condicion de salida por cantidad de muestras
            if count and muestras >= count:
                print(f"Listo: {muestras} muestras.")
                return
            # Condicion de salida por tiempo
            if seconds and (time.time() - inicio) >= seconds:
                print(f"Listo: {muestras} muestras en {seconds}s.")
                return

            # Leer una linea del ESP32 y parsearla
            line = ser.readline().decode(errors="replace").strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except:
                continue                # Linea corrupta, seguir leyendo

            # Guardar en CSV si esta habilitado
            if csvw is not None:
                guardar_csv(csvw, data)

            # Guardar en log si esta habilitado
            if flog is not None and data.get("t") == "data":
                flog.write(line + "\n")
                flog.flush()            # Forzar escritura al disco

            # Solo contar y mostrar tramas de datos
            if data.get("t") == "data":
                muestras += 1
                procesar(data)

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================
def main():
    """Punto de entrada: parsea argumentos y ejecuta el bucle de lectura."""
    ap = argparse.ArgumentParser(description="Lector de datos del ESP32-C3")
    ap.add_argument("--port", default=None, help="Puerto serial (ej: /dev/ttyUSB0)")
    ap.add_argument("--csv", default=None, help="Archivo CSV de salida")
    ap.add_argument("--log", default=None, help="Archivo log de salida")
    ap.add_argument("--seconds", type=int, default=0, help="Duracion en segundos")
    ap.add_argument("--count", type=int, default=0, help="Numero de muestras")
    args = ap.parse_args()

    # Determinar el puerto (auto-deteccion si no se paso)
    port = args.port or detect_port()
    if not port:
        print("ERROR: No se detecto puerto serial.")
        sys.exit(1)

    # Abrir archivos de salida si se pidieron
    csvf = open(args.csv, "w", newline="") if args.csv else None
    csvw = csv.writer(csvf) if csvf else None
    if csvf:
        # Escribir cabecera con las claves de los campos
        csvw.writerow(["fecha_hora", "SOC", "Vbat", "Ibat", "PV1_V", "PV1_I",
                       "PV1_P", "PV_P", "Carga", "Chg_P", "Estado", "Grid_V",
                       "Grid_I", "Grid_Hz", "Inv_V", "Inv_I", "Inv_Hz",
                       "Load_I", "Load_P", "Load_VA", "T_DCDC", "T_DCAC",
                       "T_Trafo", "T_Amb", "PV_hoy", "Load_hoy"])
    logf = open(args.log, "w") if args.log else None

    try:
        loop_lectura(port, csvw, logf, args.seconds, args.count)
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario.")
    finally:
        # Cerrar archivos abiertos
        if csvf: csvf.close()
        if logf: logf.close()

if __name__ == "__main__":
    main()
