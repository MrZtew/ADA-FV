# Proyectos de Referencia — Inversores por Modbus RS485

Proyectos open-source que implementan comunicación Modbus RTU con inversores solares usando ESP32. Sirven como referencia de arquitectura para el MonitorFV.

## Tabla de proyectos

| Marca | Proyecto | Plataforma | Enlace |
|-------|----------|-----------|--------|
| SRNE | SRNE inverters by Modbus RS485 | ESPhome + ESP32-S3 | [phinix-org/SRNE-inverters-by-modbus-rs485](https://github.com/phinix-org/SRNE-inverters-by-modbus-rs485) |
| Growatt | Growatt ESPHome ESP32 Modbus RS485 | ESPhome + ESP32 | [JasperE84/Growatt_ESPHome_ESP32_Modbus_RS485_Example](https://github.com/JasperE84/Growatt_ESPHome_ESP32_Modbus_RS485_Example) |
| Deye / Sunsynk | Deye ESP32 Bridge | ESP32 (nativo) | [bagges/deye-esp32-bridge](https://github.com/bagges/deye-esp32-bridge) |
| GoodWe | Edge device (tesis) | ESP32 | Proyecto validado con inversor real |
| Sungrow | Modbus RTU | — | Documentación disponible |
| Solax | Solax Modbus Gateway | ESP32 → MQTT | [tobiasfaust/SolaxModbusGateway](https://github.com/tobiasfaust/SolaxModbusGateway) |
| SolArk | SolArk ESPHome | ESPhome | [chuyskywalker/solark-esphome](https://github.com/chuyskywalker/solark-esphome) |

## Patrones comunes identificados

- **Módulo RS485** conectado a UART del ESP32 (pines GPIO16/17 o RX/TX genéricos)
- **Módulo convertidor** generalmente MAX3485 (3.3V) o MAX485
- **Conexión al inversor** vía puerto RJ45 o terminales DB9
- **Parámetros típicos**: 9600 baud, 8N1, dirección por defecto 1
- **Máx. registros por trama**: 32 (limitación común en inversores chinos)
- **MQTT/ESPhome** como capa de integración con Home Assistant
