#!/usr/bin/env python3
"""
Herramienta de prueba de comunicacion Modbus RTU para inversores SRNE HF2430U80-H
Universidad del Magdalena — Proyecto de Grado: Monitor FV Aulas Sostenibles

USO:
  python test_modbus_srne.py                     # auto-detect puerto, lectura unica
  python test_modbus_srne.py /dev/ttyUSB0        # puerto especifico, lectura unica
  python test_modbus_srne.py /dev/ttyUSB0 --loop  # modo monitor continuo (cada 5s)
  python test_modbus_srne.py /dev/ttyUSB0 --loop --interval 10  # cada 10 segundos
"""

import sys
import time
import struct
import argparse
from datetime import datetime

from pymodbus.client import ModbusSerialClient

# ─── Mapa completo de registros ───────────────────────────────────────────────

# Cada grupo: (nombre, [(dir, nombre_reg, count, tipo, factor, unidad, decodificador), ...])
# tipos: U16, S16, STRING
# decodificador opcional: funcion que recibe el valor y retorna string descriptivo

MACH_TYPES = {
    0: "Domestic controller", 1: "Street light controller",
    3: "Grid-connected inverter", 4: "All-in-one solar charger inverter",
    5: "Power frequency off-grid",
}

MACHINE_STATES = {
    0: "Power-on delay", 1: "Standby", 2: "Initialization",
    3: "Soft start", 4: "AC power operation", 5: "Inverter operation",
    6: "Inverter to AC power", 7: "AC power to inverter",
    8: "Battery activation", 9: "Manual shutdown", 10: "Fault",
}

CHARGE_STATES = {
    0: "Charge off", 1: "Quick charge", 2: "Constant voltage charge",
    4: "Float charge", 6: "Li battery activate", 8: "Full",
}

PRIORITY_FLAGS = {0: "No password", 1: "User password", 4: "Manufacturer password"}

PRODUCT_AREAS = {0: "Shenzhen", 1: "Dongguan"}

REGISTER_GROUPS = [
    ("P00 — Product Info (Version, SN, Fabricacion)", [
        (0x000A, "MinorVersion",          1, "U16", 1,    "",      None),
        (0x000B, "MachType",              1, "U16", 1,    "",      lambda v: MACH_TYPES.get(v, f"Unknown({v})")),
        (0x0012, "AfciFirmwareVersion",   1, "U16", 1,    "",      None),
        (0x0013, "AfciAlgorithmVersion",  1, "U16", 1,    "",      None),
        (0x0014, "SoftWareVersion(APP)",  1, "U16", 1,    "",      lambda v: f"V{v//100}.{v%100:02d}"),
        (0x0015, "BootloaderVersion",     1, "U16", 1,    "",      lambda v: f"V{v//100}.{v%100:02d}"),
        (0x0016, "HardWareVersion(Control)",1, "U16", 1,    "",    lambda v: f"V{v//100}.{v%100:02d}"),
        (0x0017, "HardWareVersion(Power)", 1, "U16", 1,    "",    lambda v: f"V{v//100}.{v%100:02d}"),
        (0x001A, "Rs485Addr",             1, "U16", 1,    "",      None),
        (0x001B, "MachModelNum2",         1, "U16", 1,    "",      None),
        (0x001C, "RS485ProtocolVersion",  1, "U16", 1,    "",      lambda v: f"V{v//100}.{v%100:02d}"),
        (0x0020, "ProductAreaCode",       1, "U16", 1,    "",      lambda v: PRODUCT_AREAS.get(v, f"Unknown({v})")),
    ]),
    ("P01 — DC Data: Bateria (SOC, Voltaje, Corriente, Temperatura)", [
        (0x0100, "BatSoc",               1, "U16", 1,    "%",     None),
        (0x0101, "BatVolt",              1, "U16", 0.1,  "V",     None),
        (0x0102, "ChargeCurr",           1, "S16", 0.1,  "A",     None),
        (0x0103, "DeviceBatTemper",      1, "S16", 0.1,  "°C",    None),
    ]),
    ("P01 — DC Data: Paneles PV (V, I, P)", [
        (0x0107, "Pv1Volt",              1, "U16", 0.1,  "V",     None),
        (0x0108, "Pv1Curr",              1, "U16", 0.1,  "A",     None),
        (0x0109, "Pv1ChargePower",       1, "U16", 1,    "W",     None),
        (0x010A, "PvTotalPower",         1, "U16", 1,    "W",     None),
        (0x010B, "ChargeState",          1, "U16", 1,    "",      lambda v: CHARGE_STATES.get(v, f"Unknown({v})")),
        (0x010E, "ChargePower",          1, "U16", 1,    "W",     None),
        (0x010F, "Pv2Volt",              1, "U16", 0.1,  "V",     None),
        (0x0110, "Pv2Curr",              1, "U16", 0.1,  "A",     None),
        (0x0111, "Pv2ChargePower",       1, "U16", 1,    "W",     None),
    ]),
    ("P01 — DC Data: BMS Bateria", [
        (0x0112, "BatBmsVolt",           1, "U16", 0.1,  "V",     None),
        (0x0113, "BatBmsCurr",           1, "U16", 0.1,  "A",     None),
        (0x0114, "BatBmsTemp",           1, "S16", 0.1,  "°C",    None),
        (0x0115, "BatBmsChgLimitVolt",   1, "U16", 0.1,  "V",     None),
        (0x0116, "BatBmsChgLimitCurr",   1, "U16", 0.1,  "A",     None),
        (0x0117, "BatBmsDchgLimitCurr",  1, "U16", 0.1,  "A",     None),
        (0x0118, "BmsAlarmH",            1, "U16", 1,    "(hex)", None),
        (0x0119, "BmsAlarmL",            1, "U16", 1,    "(hex)", None),
        (0x011A, "BmsProtectH",          1, "U16", 1,    "(hex)", None),
        (0x011B, "BmsProtectL",          1, "U16", 1,    "(hex)", None),
        (0x012F, "BmsSwVer",             1, "U16", 1,    "",      None),
        (0x0130, "BmsHwVer",             1, "U16", 1,    "",      None),
    ]),
    ("P01 — DC Data: PV3-PV6 + Batt2 (extendido)", [
        (0x011C, "Batt2Volt",            1, "U16", 0.1,  "V",     None),
        (0x011D, "Batt2Curr",            1, "S16", 0.1,  "A",     None),
        (0x011E, "Pv3Volt",              1, "U16", 0.1,  "V",     None),
        (0x011F, "Pv3Curr",              1, "U16", 0.1,  "A",     None),
        (0x0120, "Pv3Power",             1, "U16", 1,    "W",     None),
        (0x0121, "Pv4Volt",              1, "U16", 0.1,  "V",     None),
        (0x0122, "Pv4Curr",              1, "U16", 0.1,  "A",     None),
        (0x0123, "Pv4Power",             1, "U16", 1,    "W",     None),
        (0x0124, "Pv5Volt",              1, "U16", 0.1,  "V",     None),
        (0x0125, "Pv5Curr",              1, "U16", 0.1,  "A",     None),
        (0x0126, "Pv5Power",             1, "U16", 1,    "W",     None),
        (0x0127, "Pv6Volt",              1, "U16", 0.1,  "V",     None),
        (0x0128, "Pv6Curr",              1, "U16", 0.1,  "A",     None),
        (0x0129, "Pv6Power",             1, "U16", 1,    "W",     None),
    ]),
    ("P02 — Inverter Data: Estado, Fallas, Tiempos", [
        (0x0200, "CurrErrReg_0",         1, "U16", 1,    "(hex)", None),
        (0x0201, "CurrErrReg_1",         1, "U16", 1,    "(hex)", None),
        (0x0202, "CurrErrReg_2",         1, "U16", 1,    "(hex)", None),
        (0x0203, "CurrErrReg_3",         1, "U16", 1,    "(hex)", None),
        (0x0204, "CurrFcode_0",          1, "U16", 1,    "",      None),
        (0x0205, "CurrFcode_1",          1, "U16", 1,    "",      None),
        (0x0206, "CurrFcode_2",          1, "U16", 1,    "",      None),
        (0x0207, "CurrFcode_3",          1, "U16", 1,    "",      None),
        (0x020F, "GridOnRemainTime",     1, "U16", 1,    "s",     None),
        (0x0210, "MachineState",         1, "U16", 1,    "",      lambda v: MACHINE_STATES.get(v, f"Unknown({v})")),
        (0x0211, "PriorityFlag",         1, "U16", 1,    "",      lambda v: PRIORITY_FLAGS.get(v, f"Unknown({v})")),
    ]),
    ("P02 — Inverter Data: Red AC (V, I, F, P)", [
        (0x0212, "BusVoltSum",           1, "U16", 0.1,  "V",     None),
        (0x0213, "GridVoltA",            1, "U16", 0.1,  "V",     None),
        (0x0214, "GridCurrA",            1, "U16", 0.1,  "A",     None),
        (0x0215, "GridFreq",             1, "U16", 0.01, "Hz",    None),
        (0x0216, "InvVoltA",             1, "U16", 0.1,  "V",     None),
        (0x0217, "InvCurrA",             1, "U16", 0.1,  "A",     None),
        (0x0218, "InvFreq",              1, "U16", 0.01, "Hz",    None),
        (0x0219, "LoadCurrA",            1, "U16", 0.1,  "A",     None),
        (0x021B, "LoadActivePowerA",     1, "U16", 1,    "W",     None),
        (0x021C, "LoadApparentPowerA",   1, "U16", 1,    "VA",    None),
        (0x021E, "LineChgCurr",          1, "U16", 0.1,  "A",     None),
        (0x021F, "LoadRatioA",           1, "U16", 1,    "%",     None),
    ]),
    ("P02 — Inverter Data: Temperaturas", [
        (0x0220, "Tempera (DC-DC)",      1, "S16", 0.1,  "°C",    None),
        (0x0221, "Temperb (DC-AC)",      1, "S16", 0.1,  "°C",    None),
        (0x0222, "Temperc (Transformador)",1, "S16", 0.1, "°C",   None),
        (0x0223, "Temperd (Ambiente)",   1, "S16", 0.1,  "°C",    None),
        (0x0224, "Ibuck1 (PV charge)",   1, "U16", 0.1,  "A",     None),
        (0x0225, "ParallCurrRms",        1, "U16", 0.1,  "A",     None),
        (0x0228, "PBusVolt",             1, "U16", 0.1,  "V",     None),
        (0x0229, "NBusVolt",             1, "U16", 0.1,  "V",     None),
    ]),
    ("P02 — Inverter Data: Fases B/C (bifasico/trifasico)", [
        (0x022A, "GridVoltB",            1, "U16", 0.1,  "V",     None),
        (0x022B, "GridVoltC",            1, "U16", 0.1,  "V",     None),
        (0x022C, "InvVoltB",             1, "U16", 0.1,  "V",     None),
        (0x022D, "InvVoltC",             1, "U16", 0.1,  "V",     None),
        (0x022E, "InvCurrB",             1, "U16", 0.1,  "A",     None),
        (0x022F, "InvCurrC",             1, "U16", 0.1,  "A",     None),
        (0x0230, "LoadCurrB",            1, "U16", 0.1,  "A",     None),
        (0x0231, "LoadCurrC",            1, "U16", 0.1,  "A",     None),
        (0x0232, "LoadActivePowerB",     1, "U16", 1,    "W",     None),
        (0x0233, "LoadActivePowerC",     1, "U16", 1,    "W",     None),
        (0x0236, "LoadRatioB",           1, "U16", 1,    "%",     None),
        (0x0237, "LoadRatioC",           1, "U16", 1,    "%",     None),
        (0x0238, "GridCurrB",            1, "U16", 0.1,  "A",     None),
        (0x0239, "GridCurrC",            1, "U16", 0.1,  "A",     None),
        (0x023A, "GridActivePowerA",     1, "S16", 1,    "W",     None),
        (0x023B, "GridActivePowerB",     1, "S16", 1,    "W",     None),
        (0x023C, "GridActivePowerC",     1, "S16", 1,    "W",     None),
        (0x023D, "GridApparentPowerA",   1, "U16", 1,    "VA",    None),
        (0x023E, "GridApparentPowerB",   1, "U16", 1,    "VA",    None),
        (0x023F, "GridApparentPowerC",   1, "U16", 1,    "VA",    None),
        (0x0240, "HomeLoadActivePowerA", 1, "U16", 1,    "W",     None),
        (0x0241, "HomeLoadActivePowerB", 1, "U16", 1,    "W",     None),
        (0x0242, "HomeLoadActivePowerC", 1, "U16", 1,    "W",     None),
    ]),
    ("P09 — Estadisticas de Energia: Hoy y Total", [
        (0xF02A, "EnergyStatisticsDay_L", 1, "U16", 0.1, "kWh",   None),
        (0xF02B, "EnergyStatisticsDay_H", 1, "U16", 0.1, "kWh",   None),
        (0xF02C, "GeneratEnergyToGridToday",1,"U16",0.1, "kWh",   None),
        (0xF02D, "BatChgAHToday",        1, "U16", 1,    "Ah",    None),
        (0xF02E, "BatDischgAHToday",     1, "U16", 1,    "Ah",    None),
        (0xF02F, "GeneratEnergyToday",   1, "U16", 0.1,  "kWh",   None),
        (0xF030, "UsedEnergyToday",      1, "U16", 0.1,  "kWh",   None),
        (0xF031, "WorkDaysTotal",        1, "U16", 1,    "dias",  None),
        (0xF04A, "InvWorkTimeTotal",     1, "U16", 1,    "h",     None),
        (0xF04B, "LineWorkTimeTotal",    1, "U16", 1,    "h",     None),
    ]),
    ("P09 — Estadisticas: Ultimos 7 dias (Energia PV)", [
        (0xF000, "PVEnergyDay1",         1, "U16", 0.1,  "kWh",   None),
        (0xF001, "PVEnergyDay2",         1, "U16", 0.1,  "kWh",   None),
        (0xF002, "PVEnergyDay3",         1, "U16", 0.1,  "kWh",   None),
        (0xF003, "PVEnergyDay4",         1, "U16", 0.1,  "kWh",   None),
        (0xF004, "PVEnergyDay5",         1, "U16", 0.1,  "kWh",   None),
        (0xF005, "PVEnergyDay6",         1, "U16", 0.1,  "kWh",   None),
        (0xF006, "PVEnergyDay7",         1, "U16", 0.1,  "kWh",   None),
    ]),
    ("P09 — Estadisticas Totales (acumulado historico)", [
        (0xF032, "GridEnergyTotal_L",    1, "U16", 0.1,  "kWh",   None),
        (0xF033, "GridEnergyTotal_H",    1, "U16", 0.1,  "kWh",   None),
        (0xF034, "BatChgAHTotal_L",      1, "U16", 1,    "Ah",    None),
        (0xF035, "BatChgAHTotal_H",      1, "U16", 1,    "Ah",    None),
        (0xF036, "BatDischgAHTotal_L",   1, "U16", 1,    "Ah",    None),
        (0xF037, "BatDischgAHTotal_H",   1, "U16", 1,    "Ah",    None),
        (0xF038, "GeneratEnergyTotal_L", 1, "U16", 0.1,  "kWh",   None),
        (0xF039, "GeneratEnergyTotal_H", 1, "U16", 0.1,  "kWh",   None),
        (0xF03A, "UsedEnergyTotal_L",    1, "U16", 0.1,  "kWh",   None),
        (0xF03B, "UsedEnergyTotal_H",    1, "U16", 0.1,  "kWh",   None),
        (0xF04E, "BatDischgkWhToday",    1, "U16", 0.1,  "kWh",   None),
        (0xF050, "BatChgkWhTotal_L",     1, "U16", 0.1,  "kWh",   None),
        (0xF051, "BatChgkWhTotal_H",     1, "U16", 0.1,  "kWh",   None),
        (0xF052, "BatDischgkWhTotal_L",  1, "U16", 0.1,  "kWh",   None),
        (0xF053, "BatDischgkWhTotal_H",  1, "U16", 0.1,  "kWh",   None),
        (0xF054, "LineChgkWhTotal_L",    1, "U16", 0.1,  "kWh",   None),
        (0xF055, "LineChgkWhTotal_H",    1, "U16", 0.1,  "kWh",   None),
        # Generador (modelos con soporte, ej: HESP120SH3)
        (0xF056, "GenLoadConsumToday",   1, "U16", 0.1,  "kWh",   None),
        (0xF057, "GenChgkWhToday",       1, "U16", 0.1,  "kWh",   None),
        (0xF05C, "GenWorkTimeToday",     1, "U16", 1,    "h",     None),
        (0xF05D, "GenWorkTimeTotal",     1, "U16", 1,    "h",     None),
    ]),
    ("P10 — Registro de Fallas (primeras 8 de 32, V2.08+)", [
        (0xF800, "Fault1_code",          1, "U16", 1,    "",      None),
        (0xF810, "Fault2_code",          1, "U16", 1,    "",      None),
        (0xF820, "Fault3_code",          1, "U16", 1,    "",      None),
        (0xF830, "Fault4_code",          1, "U16", 1,    "",      None),
        (0xF840, "Fault5_code",          1, "U16", 1,    "",      None),
        (0xF850, "Fault6_code",          1, "U16", 1,    "",      None),
        (0xF860, "Fault7_code",          1, "U16", 1,    "",      None),
        (0xF870, "Fault8_code",          1, "U16", 1,    "",      None),
        # Cada bloque de falla ocupa 16 regs (F800+16*n)
        # Los 3 regs siguientes = sello de tiempo (año/mes, día/hora, min/seg)
        # Los 12 regs restantes = datos capturados al fallar
        (0xF801, "Fault1_time_YM",       1, "U16", 1,    "",      None),
        (0xF802, "Fault1_time_DH",       1, "U16", 1,    "",      None),
        (0xF803, "Fault1_time_MS",       1, "U16", 1,    "",      None),
    ]),
]


# ─── Funciones auxiliares ─────────────────────────────────────────────────────

def decode_s16(val):
    return val if val < 0x8000 else val - 0x10000


def format_reg_value(reg, raw):
    *_, stype, factor, unit, decoder = reg
    if raw is None:
        return None
    if stype == "S16":
        val = decode_s16(raw)
    else:
        val = raw
    scaled = val * factor
    return scaled


def format_reg_text(reg, scaled_val, raw):
    name = reg[1]
    unit = reg[5]
    decoder = reg[6]

    if scaled_val is None:
        return f"  {name:<36s} ---"

    # Formatear segun factor
    if isinstance(scaled_val, float) and reg[4] < 1:
        # Con decimales
        if reg[4] < 0.1:
            s = f"{scaled_val:.2f}"
        else:
            s = f"{scaled_val:.1f}"
    else:
        s = str(int(scaled_val))

    text = f"  {name:<36s} {s:>10s}"
    if unit:
        text += f" {unit}"
    else:
        text += "  "

    # Decodificador
    if decoder and raw is not None:
        decoded = decoder(raw)
        if decoded:
            text += f"  ({decoded})"

    return text


def auto_detect_port():
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        if not ports:
            return None
        # Preferir los que mencionan 485/usb/serial
        for p in ports:
            desc = p.description.lower()
            if any(kw in desc for kw in ["485", "usb", "serial", "uart", "ftdi", "ch340", "cp210"]):
                return p.device
        return ports[0].device
    except ImportError:
        return None


def try_read_regs(client, addr, count, device_id=1, max_retries=2):
    for attempt in range(max_retries):
        try:
            resp = client.read_holding_registers(addr, count=count, device_id=device_id)
            if resp and not resp.isError():
                return resp.registers
        except Exception:
            pass
        time.sleep(0.05)
    return None


def read_group_batch(client, regs, device_id=1):
    """Lee un grupo de registros, bachleando solo bloques consecutivos."""
    if not regs:
        return {}
    results = {}
    i = 0
    while i < len(regs):
        # Buscar bloque consecutivo (sin gaps)
        block_start = i
        block_addr = regs[i][0]
        block_len = 1
        j = i + 1
        while j < len(regs) and regs[j][0] == regs[j-1][0] + 1 and block_len < 32:
            block_len += 1
            j += 1

        if block_len > 1:
            # Lectura por lotes
            raw = try_read_regs(client, block_addr, block_len, device_id=device_id)
            if raw is not None:
                for k in range(block_len):
                    results[block_addr + k] = raw[k]
            else:
                for k in range(block_len):
                    r = try_read_regs(client, block_addr + k, 1, device_id=device_id)
                    results[block_addr + k] = r[0] if r else None
            i = j
        else:
            # Lectura individual
            r = try_read_regs(client, regs[i][0], 1, device_id=device_id)
            results[regs[i][0]] = r[0] if r else None
            i += 1
    return results


def read_all(client, device_id=1):
    """Lee todos los grupos de registros."""
    output = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output.append(f"═══════════════════════════════════════════════════════════════")
    output.append(f"  Monitor FV — Prueba Modbus RTU SRNE HF2430U80-H")
    output.append(f"  {timestamp}")
    output.append(f"═══════════════════════════════════════════════════════════════\n")

    success_count = 0
    fail_count = 0

    for group_name, regs in REGISTER_GROUPS:
        output.append(f"─── {group_name} ───")
        results = read_group_batch(client, regs, device_id=device_id)

        group_ok = 0
        for reg in regs:
            addr = reg[0]
            raw = results.get(addr)
            scaled = format_reg_value(reg, raw)
            text = format_reg_text(reg, scaled, raw)
            output.append(text)
            if raw is not None:
                group_ok += 1

        if group_ok == 0:
            output.append(f"  {"":<36s} (sin respuesta)")
        output.append("")
        success_count += group_ok
        fail_count += len(regs) - group_ok

    output.append(f"─── Resumen ───")
    output.append(f"  Registros leidos OK:  {success_count}")
    output.append(f"  Registros sin respuesta: {fail_count}")
    output.append(f"  Total: {success_count + fail_count}")
    output.append("")

    return "\n".join(output)


def monitor_loop(client, device_id=1, interval=5):
    """Modo monitor continuo: muestra solo los registros criticos cada N segundos."""
    critical_regs = [
        (0x0100, "BatSoc",          1, "U16", 1,   "%"),
        (0x0101, "BatVolt",         1, "U16", 0.1, "V"),
        (0x0102, "ChargeCurr",      1, "S16", 0.1, "A"),
        (0x0103, "DeviceBatTemper", 1, "S16", 0.1, "°C"),
        (0x0107, "Pv1Volt",         1, "U16", 0.1, "V"),
        (0x0109, "Pv1ChargePower",  1, "U16", 1,   "W"),
        (0x010A, "PvTotalPower",    1, "U16", 1,   "W"),
        (0x010B, "ChargeState",     1, "U16", 1,   ""),
        (0x0210, "MachineState",    1, "U16", 1,   ""),
        (0x0213, "GridVoltA",       1, "U16", 0.1, "V"),
        (0x021B, "LoadActivePowerA",1, "U16", 1,   "W"),
        (0x0220, "Tempera(DC-DC)",  1, "S16", 0.1, "°C"),
        (0x0223, "TempAmbiente",    1, "S16", 0.1, "°C"),
    ]

    try:
        while True:
            now = datetime.now().strftime("%H:%M:%S")
            print(f"\r{'='*70}", end="")
            print(f"\r[{now}] ", end="")

            results = read_group_batch(client, critical_regs, device_id=device_id)
            line_parts = []
            for reg in critical_regs:
                addr = reg[0]
                raw = results.get(addr)
                scaled = format_reg_value(reg, raw)
                name = reg[1]
                unit = reg[5]

                if scaled is None:
                    val_str = "---"
                elif isinstance(scaled, float):
                    val_str = f"{scaled:.1f}"
                else:
                    val_str = str(int(scaled))

                if addr == 0x010B and raw is not None:
                    val_str = CHARGE_STATES.get(raw, f"{raw}")
                if addr == 0x0210 and raw is not None:
                    val_str = MACHINE_STATES.get(raw, f"{raw}")

                line_parts.append(f"{name}={val_str}{unit}")

            print(" | ".join(line_parts), end="", flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nMonitor detenido.")


# ─── Punto de entrada ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Herramienta de prueba Modbus RTU para inversores SRNE HF2430U80-H"
    )
    parser.add_argument("port", nargs="?", default=None,
                        help="Puerto serial (ej: /dev/ttyUSB0)")
    parser.add_argument("--loop", action="store_true",
                        help="Modo monitor continuo")
    parser.add_argument("--interval", type=int, default=5,
                        help="Intervalo en segundos para modo loop (default: 5)")
    parser.add_argument("--slave", "--device_id", type=int, default=1, dest="device_id",
                        help="Direccion Modbus del inversor (default: 1)")
    parser.add_argument("--baud", type=int, default=9600,
                        help="Baud rate (default: 9600)")

    args = parser.parse_args()

    # Detectar puerto
    port = args.port
    if not port:
        port = auto_detect_port()
    if not port:
        print("ERROR: No se detecto puerto serial.")
        print("  Usa: python test_modbus_srne.py /dev/ttyUSB0")
        print("  O verifica con: ls /dev/ttyUSB*")
        sys.exit(1)

    print(f"Conectando a {port} ({args.baud} 8N1, device_id={args.device_id})...")
    client = ModbusSerialClient(
        port=port, baudrate=args.baud, bytesize=8,
        parity='N', stopbits=1, timeout=2,
    )

    if not client.connect():
        print(f"ERROR: No se pudo abrir {port}")
        print(f"  Prueba: sudo chmod 666 {port}")
        print(f"  Verifica: ls -l {port}")
        sys.exit(1)

    # Prueba rapida: leer protocol version para verificar comunicacion
    print("Verificando comunicacion...")
    test = try_read_regs(client, 0x001C, 1, device_id=args.device_id)
    if test is None:
        print("⚠ NO HAY RESPUESTA del inversor.")
        print("  Verifica:")
        print("  1. Conexion A(Blanco/Naranja) → Pin7 RJ45")
        print("  2. Conexion B(Naranja) → Pin8 RJ45")
        print("  3. El inversor esta encendido")
        print("  4. Direccion Modbus correcta (--slave)")
        client.close()
        sys.exit(1)

    proto_raw = test[0]
    proto_major = proto_raw // 100
    proto_minor = proto_raw % 100
    print(f"Comunicacion OK — Protocolo V{proto_major}.{proto_minor:02d}\n")

    if args.loop:
        print("Modo monitor continuo (Ctrl+C para detener)...\n")
        monitor_loop(client, device_id=args.device_id, interval=args.interval)
    else:
        output = read_all(client, device_id=args.device_id)
        print(output)

        # Guardar a archivo
        filename = f"modbus_dump_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, "w") as f:
            f.write(output)
        print(f"Log guardado: {filename}")

    client.close()


if __name__ == "__main__":
    main()
