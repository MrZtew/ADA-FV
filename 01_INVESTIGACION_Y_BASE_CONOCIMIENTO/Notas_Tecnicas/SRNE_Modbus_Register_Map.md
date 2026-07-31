# Mapa de Registros Modbus — SRNE HF2430U80-H

Basado en: SRNE Solar MODBUS Protocol V2.08 + integración ESPhome de phinix-org.

## Parámetros de comunicación

| Parámetro | Valor |
|-----------|-------|
| Baud rate | 9600 |
| Data bits | 8 |
| Parity | None |
| Stop bits | 1 |
| Addr. default | 0x01 |
| Max registros/lectura | 32 |

## P00 — Product Info (0x000A–0x0049)

| Dir | Nombre | Acceso | Unidad | Factor | Tipo |
|-----|--------|--------|--------|--------|------|
| 0x000A | MinorVersion | R | - | 1 | U_WORD |
| 0x000B | MachType | R | - | 1 | U_WORD |
| 0x0012 | AfciFirmwareVersion | R | - | 1 | U_WORD |
| 0x0013 | AfciAlgorithmVersion | R | - | 1 | U_WORD |
| 0x0014 | SoftWareVersion (APP) | R | - | 1 | U_WORD |
| 0x0015 | BootloaderVersion | R | - | 1 | U_WORD |
| 0x0016 | HardWareVersion (ControlPanel) | R | - | 1 | U_WORD |
| 0x0017 | HardWareVersion (PowerAmp) | R | - | 1 | U_WORD |
| 0x001A | Rs485Addr | R | - | 1 | U_WORD |
| 0x001B | MachModelNum2 | R | - | 1 | U_WORD |
| 0x001C | RS485ProtocolVersion | R | - | 1 | U_WORD |
| 0x001E | ManufactureDate_YM | R | - | - | U_WORD | year(hi), month(lo) |
| 0x001F | ManufactureDate_DH | R | - | - | U_WORD | day(hi), hour(lo) |
| 0x0020 | ProductAreaCode | R | - | 1 | U_WORD |
| 0x0021 | CpuBuildTime (20 regs) | R | - | string | - |
| 0x0035 | ProductSN (20 regs) | R | - | string | - |
| 0x004A | Cpu2BuildTime (20 regs) | R | - | string | - |

## P01 — DC Data (0x0100–0x0139)

| Dir | Nombre | Acceso | Unidad | Factor | Tipo |
|-----|--------|--------|--------|--------|------|
| 0x0100 | BatSoc | R | % | 1 | U_WORD |
| 0x0101 | BatVolt | R | V | 0.1 | U_WORD |
| 0x0102 | ChargeCurr | R | A | 0.1 | S_WORD |
| 0x0103 | DeviceBatTemper | R | °C | 0.1 | S_WORD |
| 0x0107 | Pv1Volt | R | V | 0.1 | U_WORD |
| 0x0108 | Pv1Curr | R | A | 0.1 | U_WORD |
| 0x0109 | Pv1ChargePower | R | W | 1 | U_WORD |
| 0x010A | PvTotalPower | R | W | 1 | U_WORD |
| 0x010B | ChargeState | R | - | 1 | U_WORD |
| 0x010E | ChargePower | R | W | 1 | U_WORD |
| 0x010F | Pv2Volt | R | V | 0.1 | U_WORD |
| 0x0110 | Pv2Curr | R | A | 0.1 | U_WORD |
| 0x0111 | Pv2ChargePower | R | W | 1 | U_WORD |
| 0x0112 | BatBmsVolt | R | V | 0.1 | U_WORD |
| 0x0113 | BatBmsCurr | R | A | 0.1 | U_WORD |
| 0x0114 | BatBmsTemp | R | °C | 0.1 | S_WORD |
| 0x0115 | BatBmsChgLimitVolt | R | V | 0.1 | U_WORD |
| 0x0116 | BatBmsChgLimitCurr | R | A | 0.1 | U_WORD |
| 0x0117 | BatBmsDchgLimitCurr | R | A | 0.1 | U_WORD |
| 0x0118 | BmsAlarmH | R | - | 1 | U_WORD |
| 0x0119 | BmsAlarmL | R | - | 1 | U_WORD |
| 0x011A | BmsProtectH | R | - | 1 | U_WORD |
| 0x011B | BmsProtectL | R | - | 1 | U_WORD |
| 0x011C–0x0129 | Pv3–Pv6 + Batt2 | R | V/A/W | 0.1 | U_WORD |

## P02 — Inverter Data (0x0200–0x0263)

| Dir | Nombre | Acceso | Unidad | Factor | Tipo |
|-----|--------|--------|--------|--------|------|
| 0x0200 | CurrErrReg (4 regs) | R | - | 1 | U_WORD |
| 0x0204 | CurrFcode (4 regs) | R | - | 1 | U_WORD |
| 0x020C | SysDateTime (3 regs) | RW | - | - | U_WORD |
| 0x020F | GridOnRemainTime | R | s | 1 | U_WORD |
| 0x0210 | MachineState | R | - | 1 | U_WORD |
| 0x0211 | PriorityFlag | R | - | 1 | U_WORD |
| 0x0212 | BusVoltSum | R | V | 0.1 | U_WORD |
| 0x0213 | GridVoltA | R | V | 0.1 | U_WORD |
| 0x0214 | GridCurrA | R | A | 0.1 | U_WORD |
| 0x0215 | GridFreq | R | Hz | 0.01 | U_WORD |
| 0x0216 | InvVoltA | R | V | 0.1 | U_WORD |
| 0x0217 | InvCurrA | R | A | 0.1 | U_WORD |
| 0x0218 | InvFreq | R | Hz | 0.01 | U_WORD |
| 0x0219 | LoadCurrA | R | A | 0.1 | U_WORD |
| 0x021A | LoadPF | R | - | 0.01 | S_WORD |
| 0x021B | LoadActivePowerA | R | W | 1 | U_WORD |
| 0x021C | LoadApparentPowerA | R | VA | 1 | U_WORD |
| 0x021E | LineChgCurr | R | A | 0.1 | U_WORD |
| 0x021F | LoadRatioA | R | % | 1 | U_WORD |
| 0x0220 | Tempera (DC-DC) | R | °C | 0.1 | S_WORD |
| 0x0221 | Temperb (DC-AC) | R | °C | 0.1 | S_WORD |
| 0x0222 | Temperc (Transformer) | R | °C | 0.1 | S_WORD |
| 0x0223 | Temperd (Ambient) | R | °C | 0.1 | S_WORD |
| 0x0224 | Ibuck1 (PV charge curr) | R | A | 0.1 | U_WORD |
| 0x0225 | ParallCurrRms | R | A | 0.1 | U_WORD |
| 0x0228 | PBusVolt | R | V | 0.1 | U_WORD |
| 0x0229 | NBusVolt | R | V | 0.1 | U_WORD |
| 0x022A–0x0242 | Fases B/C (V, I, P) | R | V/A/W/VA | 0.1 | U/S_WORD |
| 0x0243–0x0263 | Extensiones (GenPort, CT, etc.) | R | V/A/W/VA | 0.1 | U_DWORD |

## P09 — Power Statistics (0xF000–0xF060)

| Dir | Nombre | Acceso | Unidad | Factor | Tipo |
|-----|--------|--------|--------|--------|------|
| 0xF000 | PVEnergyLast7day (7 regs) | R | kWh | 0.1 | U_WORD |
| 0xF007 | BatChgEnergyLast7day (7 regs) | R | Ah | 1 | U_WORD |
| 0xF00E | BatDisChgEnergyLast7day (7) | R | Ah | 1 | U_WORD |
| 0xF015 | LineChgEnergyLast7day (7) | R | Ah | 1 | U_WORD |
| 0xF01C | LoadConsumLast7day (7) | R | kWh | 0.1 | U_WORD |
| 0xF023 | LoadConsumFromLineLast7day (7) | R | kWh | 0.1 | U_WORD |
| 0xF02A | EnergyStatisticsDay (2 regs) | R | kWh | 0.1 | U_DWORD |
| 0xF02C | GeneratEnergyToGridToday | R | kWh | 0.1 | U_WORD |
| 0xF02D | BatChgAHToday | R | Ah | 1 | U_WORD |
| 0xF02E | BatDischgAHToday | R | Ah | 1 | U_WORD |
| 0xF02F | GeneratEnergyToday | R | kWh | 0.1 | U_WORD |
| 0xF030 | UsedEnergyToday | R | kWh | 0.1 | U_WORD |
| 0xF031 | WorkDaysTotal | R | day | 1 | U_WORD |
| 0xF032 | GridEnergyTotal (2 regs) | R | kWh | 0.1 | U_DWORD |
| 0xF034 | BatChgAHTotal (2 regs) | R | Ah | 1 | U_DWORD |
| 0xF036 | BatDischgAHTotal (2 regs) | R | Ah | 1 | U_DWORD |
| 0xF038 | GeneratEnergyTotal (2 regs) | R | kWh | 0.1 | U_DWORD |
| 0xF03A | UsedEnergyTotal (2 regs) | R | kWh | 0.1 | U_DWORD |
| 0xF03C | LineChgEnergyTday | R | Ah | 1 | U_WORD |
| 0xF03D | LoadConsumLineTday | R | kWh | 0.1 | U_WORD |
| 0xF03E | InvWorkTimeToday | R | min | 1 | U_WORD |
| 0xF03F | LineWorkTimeToday | R | min | 1 | U_WORD |
| 0xF040 | PowerOnTime (3 regs) | R | - | - | U_WORD |
| 0xF043 | LastEquaChgTime (3 regs) | R | - | - | U_WORD |
| 0xF046 | LineChgEnergyTotal (2 regs) | R | Ah | 1 | U_DWORD |
| 0xF048 | LoadConsumLineTotal (2 regs) | R | kWh | 0.1 | U_DWORD |
| 0xF04A | InvWorkTimeTotal | R | h | 1 | U_WORD |
| 0xF04B | LineWorkTimeTotal | R | h | 1 | U_WORD |
| 0xF04C | LineChgKwHTday | R | kWh | 0.1 | U_WORD |
| 0xF04E | BatDischgkWhToday | R | kWh | 0.1 | U_WORD |
| 0xF050 | BatChgkWhTotal (2 regs) | R | kWh | 0.1 | U_DWORD |
| 0xF052 | BatDischgkWhTotal (2 regs) | R | kWh | 0.1 | U_DWORD |
| 0xF054 | LineChgkWhTotal (2 regs) | R | kWh | 0.1 | U_DWORD |
| 0xF056 | GenLoadConsumToday | R | kWh | 0.1 | U_WORD |
| 0xF057 | GenChgkWhToday | R | kWh | 0.1 | U_WORD |
| 0xF058 | GenLoadConsumTotal (2) | R | kWh | 0.1 | U_DWORD |
| 0xF05A | GenChgkWhTotal (2) | R | kWh | 0.1 | U_DWORD |
| 0xF05C | GenWorkTimeToday | R | h | 1 | U_WORD |
| 0xF05D | GenWorkTimeTotal | R | h | 1 | U_WORD |
| 0xF05E | HomdLoadConsumTday | R | kWh | 0.1 | U_WORD |
| 0xF060 | HomdLoadConsumTotal (2) | R | kWh | 0.1 | U_DWORD |

## P10 — Fault Records (0xF800–0xFA11)

**Nota importante:** El formato de registros de falla depende de la versión del protocolo.

- **V2.08+**: 32 registros de falla, cada uno ocupa 16 registros (F800-F9FF).  
  El primer registro de cada bloque es el código de falla, seguido de sello de tiempo  
  (3 regs: año/mes, día/hora, min/seg) y 12 registros de datos capturados.
  
  | Dir | Registro | Longitud | Descripción |
  |-----|----------|----------|-------------|
  | 0xF800 | FaultRecord0 | 16 regs | Código falla + tiempo + 12 datos |
  | 0xF810 | FaultRecord1 | 16 regs | (cada 16 regs = 1 falla) |
  | ... | (hasta 32 registros) | ... | ... |
  | 0xF9F0 | FaultRecord31 | 16 regs | Último registro |

- **V2.04 y anteriores**: 8 códigos de falla simples en 0xF800–0xF807.

Tabla de códigos de falla en `Referencias_Bibliograficas/MODBUS Protocol for Energy Storage Inverter - Fault Codes Table.csv`.

## MachineState (0x0210)

| Valor | Estado |
|-------|--------|
| 0 | Power-on delay |
| 1 | Standby |
| 2 | Initialization |
| 3 | Soft start |
| 4 | AC power operation |
| 5 | Inverter operation |
| 6 | Inverter to AC power |
| 7 | AC power to inverter |
| 8 | Battery activation |
| 9 | Manual shutdown |
| 10 | Fault |

## ChargeState (0x010B)

| Valor | Estado |
|-------|--------|
| 0 | Charge off |
| 1 | Quick charge |
| 2 | Constant voltage charge |
| 4 | Float charge |
| 6 | Li battery activate |
| 8 | Full |

## Archivos ESPhome de referencia

Disponibles en el repositorio clonado (`/tmp/srne-modbus/include/`):

| Archivo | Contenido |
|---------|-----------|
| `full/P00-ProductInfo/SR-000A-0049-sensors.yaml` | Info de producto, versión, SN |
| `full/P01-DC-Data/SR-0100-0111-sensors.yaml` | Datos DC (batería, paneles) |
| `full/P02-InverterData/SR-0200-0210-text_sensor.yaml` | Estado, fallas, fecha |
| `full/P02-InverterData/SR-0211-0243-sensor.yaml` | Tensión, corriente, potencia AC |
| `full/P05-SettingBattery-related/*.yaml` | Configuración batería |
| `full/P07-SettingInverter-User/*.yaml` | Configuración usuario |
| `full/P08-SettingInverter-Grid/*.yaml` | Configuración red |
| `full/P09-PowerStatstics/*.yaml` | Estadísticas históricas |
| `full/P10-FaultRecord/*.yaml` | Registro de fallas |
| `modules/P03-DeviceControl/*.yaml` | Control del dispositivo |
