# Firmware — Monitor FV

Firmware del ESP32-C3 para el monitor de potencia fotovoltaica
del inversor SRNE HF2430U80-H.

## Firmware principal

- `esp32c3_srne_modbus.ino` — Lee los registros Modbus RTU del inversor
  (9600 baud, 8N1, dirección 1) a través de un módulo RS485 auto-dirección
  y reenvía los valores ya escalados como JSON por el USB Serial a 115200 baud.

  Formato de salida (una línea por muestreo, ~5 por segundo):
  ```json
  {"t":"data","ms":1234,"samples":{"SOC":100,"Vbat":27.9,"PV_P":129,"Load_P":165,...}}
  ```

  Conexión del módulo RS485 al ESP32-C3:
  | ESP32-C3 | Módulo RS485 |
  |----------|--------------|
  | GPIO6 (TX) | TX |
  | GPIO7 (RX) | RX |
  | 3.3V | VCC |
  | GND | GND |
  | | A — RJ45 pin 7 |
  | | B — RJ45 pin 8 |

  El módulo RS485 conmuta TX/RX automáticamente, por lo que no se usa
  ningún pin de control DE/RE.

## Software de PC

Los scripts para leer, mostrar y registrar estos datos están en
`04_SOFTWARE_PC/` (dashboardesp.py, reader_srne.py, serverweb_srne.py,
debug_serial.py).

## Referencias

- `esphome_reference/` — Configuraciones ESPhome de referencia para inversores SRNE
- `include/`, `lib/`, `src/` — Estructura base del proyecto PlatformIO
