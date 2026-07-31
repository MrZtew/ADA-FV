#!/usr/bin/env python3
"""
============================================================================
Depurador serial para el Monitor FV — SRNE HF2430U80-H via ESP32-C3
============================================================================

PROPOSITO:
  Mostrar en consola las lineas JSON CRUDAS que el ESP32-C3 envia por
  USB Serial, sin interpretarlas ni formatearlas. Sirve para depurar
  el firmware o verificar que el ESP32 esta transmitiendo.

ARQUITECTURA:
  ESP32-C3 --(JSON por USB Serial)--> este script

USO:
  python3 debug_serial.py                 # auto-detecta el puerto
  python3 debug_serial.py /dev/ttyUSB0    # puerto explicito
  python3 debug_serial.py --count 20      # Mostrar solo 20 lineas

SALIR:
  Ctrl+C
============================================================================
"""

import sys          # Salida del programa
import argparse     # Opciones de linea de comandos
import serial       # Comunicacion serial con el ESP32-C3
import serial.tools.list_ports  # Deteccion automatica de puertos

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
    """Punto de entrada: abre el puerto y vuelca las lineas crudas."""
    ap = argparse.ArgumentParser(description="Debug serial del ESP32-C3")
    ap.add_argument("port", nargs="?", default=None,
                    help="Puerto serial (auto-detecta si se omite)")
    ap.add_argument("--count", type=int, default=0,
                    help="Numero de lineas a mostrar (0 = infinito)")
    args = ap.parse_args()

    # Determinar el puerto serial
    port = args.port or detect_port()
    if not port:
        print("ERROR: No se detecto puerto serial.")
        sys.exit(1)

    print(f"Escuchando en {port} @115200 baud. Ctrl+C para salir.\n")

    # Abrir el puerto y volcar lineas crudas
    with serial.Serial(port, 115200, timeout=5) as ser:
        n = 0
        while True:
            line = ser.readline().decode(errors="replace").strip()
            if not line:
                continue
            print(line)                      # Volcar la linea tal cual
            n += 1
            if args.count and n >= args.count:
                print(f"\nListo: {n} lineas.")
                return

if __name__ == "__main__":
    main()
