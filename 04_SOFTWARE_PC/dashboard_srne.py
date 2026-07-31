#!/usr/bin/env python3
"""
============================================================================
Dashboard en terminal (curses) para el inversor SRNE HF2430U80-H
Comunicacion MODBUS RTU directa desde el PC
============================================================================

PROPOSITO:
  Conectarse DIRECTAMENTE al inversor via un adaptador USB-RS485 y mostrar
  los registros Modbus en tiempo real en la terminal (curses).

DIFERENCIA CON dashboardesp.py:
  - Este script habla Modbus directamente (necesita USB-RS485 + pymodbus).
  - dashboardesp.py lee el JSON de un ESP32-C3 (sin hablar Modbus).

ARQUITECTURA:
  PC --(USB-RS485)--> Inversor SRNE (Modbus RTU)

REQUISITOS:
  pip install pymodbus pyserial

USO:
  python3 dashboard_srne.py                     # auto-detecta puerto
  python3 dashboard_srne.py /dev/ttyUSB0        # puerto explicito
  python3 dashboard_srne.py /dev/ttyUSB0 1      # puerto + direccion modbus

TECLAS:
  Q  -> salir
============================================================================
"""

import sys          # Argumentos de linea de comandos
import time         # Pausas entre lecturas
import curses       # Interfaz de terminal en tiempo real
from datetime import datetime   # Marca de tiempo para la cabecera
from pymodbus.client import ModbusSerialClient  # Cliente Modbus RTU

# ============================================================================
# REGISTROS CRITICOS PARA EL DASHBOARD
# ============================================================================
# Cada entrada: (addr, nombre, unidad, factor, signed, decimales)
# A diferencia de dashboardesp.py, aqui los valores son CRUDOS del inversor,
# por lo que se debe aplicar factor y conversion signed manualmente.
REGS = [
    # --- Bateria (P01) ---
    (0x0100, "SOC",             "%",     1,   False, 0),  # Estado de carga [%]
    (0x0101, "Vbat",            "V",     0.1, False, 1),  # Voltaje bateria [V]
    (0x0102, "Ibat",            "A",     0.1, True,  1),  # Corriente bateria [A]
    (0x0103, "Tbat",            "°C",    0.1, True,  1),  # Temp. bateria [C]
    # --- Panel solar (P01) ---
    (0x0107, "PV1 V",           "V",     0.1, False, 1),  # Voltaje panel [V]
    (0x0108, "PV1 I",           "A",     0.1, False, 1),  # Corriente panel [A]
    (0x0109, "PV1 P",           "W",     1,   False, 0),  # Potencia panel [W]
    (0x010A, "PV total P",      "W",     1,   False, 0),  # Potencia PV total [W]
    (0x010B, "Carga",           "",      1,   False, 0),  # Estado de carga
    (0x010E, "Charge P",        "W",     1,   False, 0),  # Potencia de carga [W]
    (0x010F, "PV2 V",           "V",     0.1, False, 1),  # Voltaje panel PV2 [V]
    # --- Inversor (P02) ---
    (0x0210, "Estado",          "",      1,   False, 0),  # Estado de maquina
    (0x0213, "Grid V",          "V",     0.1, False, 1),  # Voltaje de red [V]
    (0x0214, "Grid I",          "A",     0.1, False, 1),  # Corriente de red [A]
    (0x0215, "Grid Hz",         "Hz",    0.01,False, 2),  # Frecuencia de red [Hz]
    (0x0216, "Inv V",           "V",     0.1, False, 1),  # Voltaje inversor [V]
    (0x0217, "Inv I",           "A",     0.1, False, 1),  # Corriente inversor [A]
    (0x0218, "Inv Hz",          "Hz",    0.01,False, 2),  # Frecuencia inversor [Hz]
    (0x0219, "Load I",          "A",     0.1, False, 1),  # Corriente de carga [A]
    (0x021B, "Load P",          "W",     1,   False, 0),  # Potencia activa [W]
    (0x021C, "Load VA",         "VA",    1,   False, 0),  # Potencia aparente [VA]
    (0x021E, "LineChg I",       "A",     0.1, False, 1),  # Corriente carga de linea [A]
    (0x021F, "Load %",          "%",     1,   False, 0),  # Porcentaje de carga [%]
    # --- Temperaturas (P02) ---
    (0x0220, "T DC-DC",         "°C",    0.1, True,  1),  # Temp. DC-DC [C]
    (0x0221, "T DC-AC",         "°C",    0.1, True,  1),  # Temp. DC-AC [C]
    (0x0222, "T Trafo",         "°C",    0.1, True,  1),  # Temp. trafo [C]
    (0x0223, "T Amb",           "°C",    0.1, True,  1),  # Temp. ambiente [C]
    # --- Bus DC (P02) ---
    (0x0224, "Ibuck1",          "A",     0.1, False, 1),  # Corriente buck [A]
    (0x0228, "PBus",            "V",     0.1, False, 1),  # Voltaje bus positivo [V]
    (0x0229, "NBus",            "V",     0.1, False, 1),  # Voltaje bus negativo [V]
    # --- Estadisticas (P09) ---
    (0xF02F, "PV hoy",          "kWh",   0.1, False, 1),  # Energia PV de hoy [kWh]
    (0xF030, "Load hoy",        "kWh",   0.1, False, 1),  # Energia consumida hoy [kWh]
    (0xF031, "Dias",            "d",     1,   False, 0),  # Dias de trabajo totales
]

# Tablas de decodificacion de codigos del inversor
ESTADOS = {0:"Power-on", 1:"Standby", 2:"Init", 3:"SoftStart",
           4:"AC op", 5:"Inverter op", 6:"Inv->AC", 7:"AC->Inv",
           8:"Bat activ", 9:"Manual off", 10:"Fault"}
CARGAS = {0:"Off", 1:"Quick", 2:"ConstV", 4:"Float", 6:"Li activ", 8:"Full"}

# ============================================================================
# LECTURA DE TODOS LOS REGISTROS VIA MODBUS
# ============================================================================
def leer(client, device_id=1):
    """Lee uno por uno los registros de la tabla REGS.

    Parametros:
        client    : cliente ModbusSerialClient ya conectado
        device_id : direccion Modbus del inversor (default 1)
    Retorna:
        dict {addr_registro: valor_crudo}
    """
    datos = {}
    for addr, name, *rest in REGS:
        try:
            # Funcion 0x03: Read Holding Registers (1 registro)
            r = client.read_holding_registers(addr, count=1, device_id=device_id)
            if r and not r.isError():
                datos[addr] = r.registers[0]    # Guardar valor crudo
        except:
            pass                                # Ignorar registros que fallen
        time.sleep(0.02)                        # Pequena pausa entre lecturas
    return datos

# ============================================================================
# FORMATEO DE UNA LINEA DEL DASHBOARD
# ============================================================================
def formatear(addr, raw):
    """Convierte un valor crudo de registro en texto legible.

    Parametros:
        addr : direccion Modbus del registro (0x...)
        raw  : valor crudo leido (None si fallo la lectura)
    """
    for r in REGS:
        if r[0] == addr:
            _, name, unit, factor, signed, dec = r
            if raw is None:
                return f"{name:>10s}: ---"

            # Conversion de complemento a 2 si el registro es signed
            val = raw if not signed else (raw if raw < 0x8000 else raw - 0x10000)
            v = val * factor                    # Aplicar factor de escala

            fmt = f"{name:>10s}: {v:.{dec}f} {unit}"

            # Anadir descripcion textual para campos de codigo
            if addr == 0x0210 and raw in ESTADOS:
                fmt += f"  ({ESTADOS[raw]})"
            if addr == 0x010B and raw in CARGAS:
                fmt += f"  ({CARGAS[raw]})"
            if addr == 0x0102 and raw is not None:
                # Convencion SRNE: positivo = descarga, negativo = carga
                sentido = "Desc" if val > 0 else "Carga"
                fmt += f" ({sentido})"
            return fmt
    return ""

# ============================================================================
# BUCLE PRINCIPAL DEL DASHBOARD (curses)
# ============================================================================
def dashboard(stdscr, port, device_id):
    """Dibuja el dashboard Modbus en tiempo real.

    Parametros:
        stdscr    : objeto de pantalla de curses
        port      : ruta del puerto serial (ej: /dev/ttyUSB0)
        device_id : direccion Modbus del inversor
    """
    # --- Configuracion de curses ---
    curses.curs_set(0)                  # Ocultar cursor
    curses.use_default_colors()
    stdscr.nodelay(1)                   # getch() sin bloqueo
    stdscr.timeout(2000)                # Timeout de teclado (2s)

    # --- Conexion Modbus RTU hacia el inversor ---
    client = ModbusSerialClient(port=port, baudrate=9600, bytesize=8,
                                parity='N', stopbits=1, timeout=2)
    if not client.connect():
        stdscr.addstr(0, 0, f"ERROR: No se pudo abrir {port}")
        stdscr.refresh()
        time.sleep(3)
        return

    # --- Leer informacion fija del inversor una sola vez ---
    info = leer(client, device_id)
    proto = info.get(0x001C, 0)         # Version del protocolo RS485
    fw = info.get(0x0014, 0)            # Version de firmware (APP)
    hw = info.get(0x0016, 0)            # Version de hardware (Control)

    while True:
        stdscr.erase()                  # Limpiar pantalla
        h, w = stdscr.getmaxyx()        # Tamano de la terminal

        # Leer todos los registros criticos en este ciclo
        datos = leer(client, device_id)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # --- Cabecera con versiones del inversor ---
        F = curses.A_BOLD
        stdscr.addstr(0, 0, "=" * min(w-1, 70), F)
        stdscr.addstr(1, 0, f"  ADA-FV - SRNE HF2430U80-H    {now}", F)
        stdscr.addstr(2, 0, f"  Puerto: {port}  Protocolo: V{proto//100}.{proto%100:02d}  "
                             f"FW: V{fw//100}.{fw%100:02d}  HW: V{hw//100}.{hw%100:02d}", F)
        stdscr.addstr(3, 0, "=" * min(w-1, 70), F)

        # --- Grupos de datos a mostrar ---
        grupos = [
            ("PANEL SOLAR",   [0x0107, 0x0108, 0x0109, 0x010A, 0x010F]),
            ("BATERIA",       [0x0100, 0x0101, 0x0102, 0x0103, 0x010B]),
            ("CARGA AC",      [0x0216, 0x0217, 0x0218, 0x0219, 0x021B, 0x021C, 0x021F]),
            ("RED",           [0x0213, 0x0214, 0x0215, 0x021E]),
            ("TEMPERATURAS",  [0x0220, 0x0221, 0x0222, 0x0223]),
            ("BUS DC",        [0x0224, 0x0228, 0x0229]),
            ("ESTADO",        [0x0210]),
            ("ENERGIA HOY",   [0xF02F, 0xF030]),
        ]

        # --- Dibujar cada grupo ---
        line = 5
        for titulo, addrs in grupos:
            if line >= h-2: break
            stdscr.addstr(line, 0, f"-- {titulo} --", F)
            line += 1
            for addr in addrs:
                if line >= h-2: break
                txt = formatear(addr, datos.get(addr))
                stdscr.addstr(line, 0, txt)
                line += 1
            line += 1

        # --- Pie de pagina ---
        if line < h-1:
            stdscr.addstr(line, 0, "=" * min(w-1, 70))
            stdscr.addstr(line+1, 0, "  Q=salir  |  Ctrl+C=salir  |  actualiza cada 2s")

        stdscr.refresh()

        # --- Esperar tecla Q (20 x 100ms = 2s) ---
        for _ in range(20):
            k = stdscr.getch()
            if k in (ord('q'), ord('Q')):
                client.close()          # Cerrar conexion Modbus
                return
            time.sleep(0.1)

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================
def main():
    """Punto de entrada: detecta el puerto y lanza el dashboard curses."""
    port = sys.argv[1] if len(sys.argv) > 1 else None
    device_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    # Deteccion automatica de puerto si no se paso por argumento
    if not port:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if any(kw in p.description.lower() for kw in ["485","usb","serial","ftdi","ch340","cp210"]):
                port = p.device
                break
        if not port and ports:
            port = ports[0].device
    if not port:
        print("ERROR: No se detecto puerto. Usa: python dashboard_srne.py /dev/ttyUSB0")
        sys.exit(1)

    curses.wrapper(dashboard, port, device_id)

if __name__ == "__main__":
    main()
