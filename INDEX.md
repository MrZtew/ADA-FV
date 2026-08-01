# Documentacion Completa — ADA-FV

Monitorizacion del inversor solar SRNE HF2430U80-H (Aulas Abiertas Sostenibles — Universidad del Magdalena).
Proyecto ADA-FV (Arquitectura de Datos para Aulas Fotovoltaicas).

## Contenido del repositorio

```
Proyecto_ADA-FV/
├── README.md                        ← Portada del repositorio
├── INDEX.md                         ← Este indice
├── 00_DOCUMENTACION_PRINCIPAL/
│   └── Manual_Tecnico_ADA-FV.md     ← MANUAL COMPLETO
├── 01_INVESTIGACION_Y_BASE_CONOCIMIENTO/
│   ├── Datasheets/                  ← Baterias (Green Point) e Inversores (SRNE)
│   ├── Notas_Tecnicas/              ← 4 notas Modbus SRNE
│   └── Referencias_Bibliograficas/  ← Papers y tablas Modbus oficiales
├── 03_FIRMWARE/
│   └── ada_fv/
│       ├── esp32c3_srne_modbus.ino  ← Firmware ESP32-C3
│       ├── platformio.ini           ← PlatformIO (esp32-c3-devkitc-02, Arduino)
│       ├── README.md
│       └── esphome_reference/       ← Modulos YAML de referencia (19)
├── 04_SOFTWARE_PC/                  ← 5 scripts Python + README
└── 05_MEDICIONES_Y_ENSAYOS/
    ├── modbus_dump_20260728_122133.txt  ← Log de prueba real
    ├── modbus_dump_20260728_122302.txt  ← Log de prueba real
    └── cap datos.png               ← Captura del dashboard en la prueba
```

## Espejo Documentacion_ADA-FV

La carpeta `~/Escritorio/Documentacion_ADA-FV/` es un **espejo por enlaces
simbolicos** de este repositorio: no contiene copias, todos sus archivos
apuntan aqui (mismo documento, se edita en cualquiera y cambia en ambos).

Regenerar el espejo (p. ej. tras reestructurar el repo):

    cd /home/sebastian/Escritorio/proyecto\ de\ grado/Proyecto_ADA-FV
    REPO=$(pwd); MIRROR=/home/sebastian/Escritorio/Documentacion_ADA-FV
    rm -rf "$MIRROR"; mkdir -p "$MIRROR"
    git ls-files -z | while IFS= read -r -d '' f; do
      mkdir -p "$MIRROR/$(dirname "$f")"; ln -s "$REPO/$f" "$MIRROR/$f"
    done

Nota: si se mueve el repositorio de ruta, los enlaces se rompen y hay que
regenerar el espejo con el comando anterior.

## Arquitectura

```
Inversor SRNE (Modbus RTU esclavo, addr 0x01, 9600 8N1)
        │
        │ RS485 (RJ45 pin 7 = A, pin 8 = B)
        │
   Modulo RS485
   (TX/RX/VCC/GND)
        │
   ESP32-C3 (GPIO6=TX1, GPIO7=RX1)
        │
        │ USB Serial (115200 baud) — JSON
        │
        ▼
   PC — Python
   ├── dashboardesp.py   → terminal curses
   └── reader_srne.py    → log CSV
```

## Flujo de datos

1. ESP32-C3 lee registros Modbus del inversor (funcion 0x03, Read Holding Registers)
2. Aplica factor de escala y conversion signed/unsigned
3. Genera JSON: `{"t":"data","ms":1234,"samples":{"SOC":100,"Vbat":27.9,...}}`
4. Envia por USB Serial a 115200 baud cada ~500ms
5. PC lee el JSON con Python

## Quick Start

```bash
# Terminal dashboard
python3 dashboardesp.py

# Log CSV
python3 reader_srne.py --log

# Debug
python3 debug_serial.py
```

## Cableado

| ESP32-C3 | Modulo RS485 | Inversor (RJ45) |
|----------|-------------|-----------------|
| GPIO6    | TX          | -               |
| GPIO7    | RX          | -               |
| 3.3V     | VCC         | -               |
| GND      | GND         | -               |
| -        | A           | Pin 7           |
| -        | B           | Pin 8           |

---
Proyecto de Grado — Universidad del Magdalena — Aulas Abiertas Sostenibles
