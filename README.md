# Sistema de Monitorización Fotovoltaica — Aulas Sostenibles

Repositorio del proyecto de grado para el diseño e implementación de un sistema de monitorización de los sistemas fotovoltaicos en las aulas sostenibles de la **Universidad del Magdalena**.

## Infraestructura objetivo

- **3 inversores modernos** (HF2430U80-H) — bancos de baterías **Green Point 25.6V 200AH**
- **4 inversores** pendientes de sensado
- **1 inversor** en espera de actualización
- Vías de comunicación: **serial** (posible software propietario) y **Modbus**

## Estructura del repositorio

- `00_DOCUMENTACION_PRINCIPAL/` — Anteproyecto, informe final, manual técnico y presentaciones
- `01_INVESTIGACION_Y_BASE_CONOCIMIENTO/` — Datasheets, notas técnicas, referencias y normas
- `02_DISENO_HARDWARE/` — Esquemáticos, PCB, simulaciones e imágenes
- `03_FIRMWARE/` — Código fuente del ESP32-C3 (`monitor_fv/esp32c3_srne_modbus.ino`)
- `04_SOFTWARE_PC/` — Scripts Python para monitorización y prueba Modbus
- `05_MEDICIONES_Y_ENSAYOS/` — Datos de validación y pruebas de laboratorio
- `06_GESTION_DEL_PROYECTO/` — Planificación, presupuesto y bitácora

## Firmware (ESP32-C3)

`03_FIRMWARE/monitor_fv/esp32c3_srne_modbus.ino` lee los registros Modbus RTU
del inversor SRNE HF2430U80-H (9600 baud, 8N1) mediante un módulo RS485
auto-dirección y los reenvía como JSON por USB Serial. Ver su README.

## Software de PC

Scripts en `04_SOFTWARE_PC/`:

| Script | Descripción |
|--------|-------------|
| `test_modbus_srne.py` | Prueba de comunicación Modbus directa (lectura completa de registros) |
| `dashboard_srne.py` | Dashboard en terminal leyendo Modbus directamente desde el PC |
| `dashboardesp.py` | Dashboard en terminal leyendo el JSON del ESP32-C3 |
| `reader_srne.py` | Lector del JSON del ESP32-C3 con opción CSV/log |
| `serverweb_srne.py` | Servidor web local (localhost:8080) con los datos en vivo |
| `debug_serial.py` | Muestra el JSON crudo del ESP32-C3 para depuración |

## Requisitos mínimos

- KiCad (esquemáticos y PCB)
- PlatformIO + ESP-IDF (firmware)
- Python 3.x + dependencias (software PC): `pymodbus`, `pyserial`

## Créditos

Proyecto de grado — Universidad del Magdalena — Autor
