# Software de PC — Monitor FV

Scripts Python para monitorizar el inversor solar SRNE HF2430U80-H
(proyecto de grado "Monitor FV — Aulas Sostenibles", Universidad del Magdalena).

## Arquitectura

Existen dos vías de lectura de datos:

1. **Modbus RTU directo desde el PC** — mediante un adaptador USB-RS485
   (CH340/CP2102). Se conecta a los pines 7 (A) y 8 (B) del puerto RJ45
   del inversor.
2. **A través del ESP32-C3** — el firmware `03_FIRMWARE/monitor_fv/esp32c3_srne_modbus.ino`
   lee el inversor por RS485 y reenvía los datos ya escalados como JSON
   por USB Serial (115200 baud).

## Scripts

| Script | Vía | Descripción |
|--------|-----|-------------|
| `test_modbus_srne.py` | Modbus directo | Prueba de comunicación: lee ~150 registros, verifica protocolo, modo monitor `--loop`, guarda dump a archivo |
| `dashboard_srne.py` | Modbus directo | Dashboard en terminal (curses) con los registros críticos en tiempo real |
| `dashboardesp.py` | ESP32-C3 | Dashboard en terminal (curses) con el JSON del ESP32 |
| `reader_srne.py` | ESP32-C3 | Lector del JSON del ESP32 con opción de guardar CSV o log |
| `serverweb_srne.py` | ESP32-C3 | Servidor web local en `http://localhost:8080` (fondo blanco, texto grande) |
| `debug_serial.py` | ESP32-C3 | Volcado del JSON crudo del ESP32 para depuración |

## Instalación

```bash
pip install pymodbus pyserial
```

## Uso rápido

```bash
# Prueba Modbus directa (auto-detecta el puerto)
python3 test_modbus_srne.py

# Dashboard Modbus directo
python3 dashboard_srne.py /dev/ttyUSB0

# Dashboard leyendo el ESP32-C3
python3 dashboardesp.py /dev/ttyUSB0

# Servidor web con los datos del ESP32
python3 serverweb_srne.py
```

## Convenciones de datos (registros SRNE)

- Voltajes y corrientes con factor 0.1 (valor Modbus × 0.1)
- Frecuencias con factor 0.01
- Temperaturas con factor 0.1, registros con signo (S16)
- Corriente de batería: positivo = descarga, negativo = carga
- Estado de máquina y estado de carga se decodifican a texto en pantalla
