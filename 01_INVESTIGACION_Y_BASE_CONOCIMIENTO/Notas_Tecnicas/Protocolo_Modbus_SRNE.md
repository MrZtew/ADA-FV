# Protocolo Modbus SRNE — HF2430U80-H

## Referencia

Repositorio de referencia: [phinix-org/SRNE-inverters-by-modbus-rs485](https://github.com/phinix-org/SRNE-inverters-by-modbus-rs485)
Protocolo: SRNE Solar MODBUS Protocol for Energy Storage Inverter V2.08

## Parámetros de comunicación serial

- Baud rate: 9600
- Data bits: 8
- Paridad: None
- Stop bits: 1
- Dirección default del inversor: 1 (0x01)
- Máximo de registros por lectura/escritura: 32 (0x20)

## Conexión RS485 vía puerto RJ45 del inversor

| Pin | Señal   |
|-----|---------|
| 1   | 5V      |
| 2   | GND     |
| 7   | RS485-A |
| 8   | RS485-B |

## Hardware probado

- **XIAO ESP32-S3** + RS485 Breakout Board (Seeed Studio) — funciona correctamente
- **Lilygo T-CAN485 ESP32** — no funciona para este caso

## Registros principales (DC Data Area — P01)

| Dirección | Variable        | Unidad | Factor |
|-----------|----------------|--------|--------|
| 0x0100    | BatSoc          | %      | 1      |
| 0x0101    | BatVolt         | V      | 0.1    |
| 0x0102    | ChargeCurr      | A      | 0.1    |
| 0x0103    | DeviceBatTemper | °C     | 0.1    |
| 0x0107    | Pv1Volt         | V      | 0.1    |
| 0x0108    | Pv1Curr         | A      | 0.1    |
| 0x0109    | Pv1ChargePower  | W      | 1      |
| 0x010A    | PvTotalPower    | W      | 1      |
| 0x010E    | ChargePower     | W      | 1      |
| 0x010F    | Pv2Volt         | V      | 0.1    |
| 0x0110    | Pv2Curr         | A      | 0.1    |
| 0x0111    | Pv2ChargePower  | W      | 1      |

## Notas importantes

- Usar `force_new_range: true` para evitar errores de comunicación Modbus
- El inversor es de tipo "Hybrid Inverter" (código 04 en MachType)
- La integración de referencia usa ESPhome + Home Assistant, pero el protocolo Modbus RTU subyacente es el mismo para cualquier implementación (ESP-IDF, Arduino, etc.)
- Los archivos de referencia de ESPhome están en `include/full/` de [phinix-org/SRNE-inverters-by-modbus-rs485](https://github.com/phinix-org/SRNE-inverters-by-modbus-rs485)
