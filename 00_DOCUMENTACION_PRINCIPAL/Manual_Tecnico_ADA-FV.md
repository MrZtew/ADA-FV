# Manual Tecnico — ADA-FV

Sistema de monitorizacion para inversor SRNE HF2430U80-H vía ESP32-C3 + RS485.
Proyecto de grado ADA-FV (Arquitectura de Datos para Aulas Fotovoltaicas) — Aulas Abiertas Sostenibles, Universidad del Magdalena.

---

## 1. Estructura del Proyecto

```
Proyecto_ADA-FV/
├── 00_DOCUMENTACION_PRINCIPAL/     ← Anteproyecto, informes, presentaciones
├── 01_INVESTIGACION_Y_BASE_CONOCIMIENTO/
│   ├── Datasheets/                  ← Hojas de datos de componentes
│   ├── Normas_y_Estandares/         ← Normas aplicables
│   ├── Notas_Tecnicas/
│   │   ├── ADC_ESP32.md
│   │   ├── Aislamiento_Galvanico.md
│   │   ├── Comparativa_Shunt_vs_Hall.md
│   │   ├── Protocolos_Modbus_USB.md
│   │   ├── Protocolo_Modbus_SRNE.md
│   │   ├── Proyectos_Referencia_Modbus_Inversores.md
│   │   ├── SRNE_Modbus_Entities.md
│   │   └── SRNE_Modbus_Register_Map.md  ← Mapa completo de registros
│   └── Referencias_Bibliograficas/
├── 02_DISENO_HARDWARE/             ← Esquematicos, PCB, imagenes
├── 03_FIRMWARE/
│   ├── ada_fv/
│   │   └── esp32c3_srne_modbus.ino ← FIRMWARE PRINCIPAL (ESP32-C3)
│   └── esphome_reference/          ← Modulos YAML de referencia
├── 04_SOFTWARE_PC/
│   ├── test_modbus_srne.py         ← Prueba de comunicacion Modbus (lectura completa)
│   ├── dashboard_srne.py           ← Dashboard curses (Modbus directo desde PC)
│   ├── dashboardesp.py             ← Dashboard curses (lee JSON del ESP32 por serial)
│   ├── reader_srne.py              ← Lector serial JSON + log CSV
│   ├── serverweb_srne.py           ← Servidor web local (serial → pagina web)
│   └── debug_serial.py             ← Debug: muestra raw del serial
├── 05_MEDICIONES_Y_ENSAYOS/        ← Datos de pruebas
├── 06_GESTION_DEL_PROYECTO/        ← Planificacion, presupuesto, bitacora
└── README.md
```

---

## 2. Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                         INVERSOR                                │
│              SRNE HF2430U80-H                                   │
│              ┌────────────────────┐                             │
│              │  Modbus RTU esclavo │                             │
│              │  Addr: 0x01        │                             │
│              │  9600 8N1          │                             │
│              │  Protocolo V1.07   │                             │
│              └────────┬───────────┘                             │
│                       │ RJ45 (pin 7=A, pin 8=B)                │
└───────────────────────┼─────────────────────────────────────────┘
                        │
                  ┌─────┴──────┐
                  │   RS485    │   A <───> RJ45-7
                  │  MODULO    │   B <───> RJ45-8
                  │  auto-dir  │
                  └──┬───┬─────┘
                     │   │
                   TX    RX
                   │     │
              ┌────┴─────┴──────┐
              │   ESP32-C3      │
              │                 │
              │  GPIO6 (TX1) ───┤ TX
              │  GPIO7 (RX1) ───┤ RX
              │                 │
              │  USB-UART (CP2102)        ───→ PC (115200 baud)
              │                 │
              └─────────────────┘

       PC: python dashboardesp.py    → Dashboard curses
       PC: python reader_srne.py     → Log CSV
       PC: python serverweb_srne.py  → http://localhost:8080
```

### Flujo de datos

1. **ESP32-C3** lee registros Modbus del inversor vía RS485 (Serial1, 9600 8N1)
2. Escala y convierte los valores (factor, signed/unsigned)
3. Envia JSON por USB Serial (Serial, 115200 baud) cada ~500ms
4. **PC** ejecuta un script Python que lee el JSON y lo muestra

### Formato JSON

```json
{"t":"data","ms":1500,"samples":{"SOC":100,"Vbat":27.9,"Ibat":-5.0,"PV1_V":129.5,...}}
```

---

## 3. Tabla de Registros Modbus (usados en el firmware)

Registros que el ESP32-C3 lee del inversor:

| Dir    | Nombre clave | Descripcion              | Factor | Signed | Unidad |
|--------|-------------|--------------------------|--------|--------|--------|
| 0x0100 | SOC         | Estado de carga bateria  | 1.0    | No     | %      |
| 0x0101 | Vbat        | Voltaje de bateria       | 0.1    | No     | V      |
| 0x0102 | Ibat        | Corriente de bateria     | 0.1    | Si     | A      |
| 0x0107 | PV1_V       | Voltaje panel PV1        | 0.1    | No     | V      |
| 0x0108 | PV1_I       | Corriente panel PV1      | 0.1    | No     | A      |
| 0x0109 | PV1_P       | Potencia panel PV1       | 1.0    | No     | W      |
| 0x010A | PV_P        | Potencia PV total        | 1.0    | No     | W      |
| 0x010B | Carga       | Estado de carga          | 1.0    | No     | -      |
| 0x010E | Chg_P       | Potencia de carga        | 1.0    | No     | W      |
| 0x0210 | Estado      | Estado de maquina        | 1.0    | No     | -      |
| 0x0213 | Grid_V      | Voltaje de red           | 0.1    | No     | V      |
| 0x0214 | Grid_I      | Corriente de red         | 0.1    | No     | A      |
| 0x0215 | Grid_Hz     | Frecuencia de red        | 0.01   | No     | Hz     |
| 0x0216 | Inv_V       | Voltaje del inversor     | 0.1    | No     | V      |
| 0x0217 | Inv_I       | Corriente del inversor   | 0.1    | No     | A      |
| 0x0218 | Inv_Hz      | Frecuencia del inversor  | 0.01   | No     | Hz     |
| 0x0219 | Load_I      | Corriente de carga       | 0.1    | No     | A      |
| 0x021B | Load_P      | Potencia activa carga    | 1.0    | No     | W      |
| 0x021C | Load_VA     | Potencia aparente carga  | 1.0    | No     | VA     |
| 0x0220 | T_DCDC      | Temperatura DC-DC        | 0.1    | Si     | C      |
| 0x0221 | T_DCAC      | Temperatura DC-AC        | 0.1    | Si     | C      |
| 0x0222 | T_Trafo     | Temperatura transformador| 0.1    | Si     | C      |
| 0x0223 | T_Amb       | Temperatura ambiente     | 0.1    | Si     | C      |
| 0xF02F | PV_hoy      | Energia PV generada hoy  | 0.1    | No     | kWh    |
| 0xF030 | Load_hoy    | Energia consumida hoy    | 0.1    | No     | kWh    |

**Nota:** Los registros Signed usan complemento a 2 (S_WORD). Positivo = descarga, negativo = carga (en Ibat).

### Mapa completo de grupos (test_modbus_srne.py)

El script de prueba `test_modbus_srne.py` lee ~150 registros organizados asi:

| Grupo | Rango | Contenido |
|-------|-------|-----------|
| P00 | 0x000A-0x0049 | Info de producto, versiones FW/HW, SN, fabricacion |
| P01 | 0x0100-0x0139 | Datos DC: bateria (SOC, V, I, T), paneles PV (V, I, P), BMS |
| P02 | 0x0200-0x0263 | Datos inversor: estado, red (V, I, Hz), carga (P, VA), temperaturas, fases B/C |
| P09 | 0xF000-0xF060 | Estadisticas: energia hoy, ultimos 7 dias, totales acumulados |
| P10 | 0xF800-0xFA11 | Registro de fallas (32 registros de 16 regs c/u en V2.08+) |

### Estados del inversor (MachineState 0x0210)

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

### Estados de carga (ChargeState 0x010B)

| Valor | Estado |
|-------|--------|
| 0 | Charge off |
| 1 | Quick charge |
| 2 | Constant voltage charge |
| 4 | Float charge |
| 6 | Li battery activate |
| 8 | Full |

---

## 4. Firmware ESP32-C3 (`esp32c3_srne_modbus.ino`)

```cpp
/*
  ADA-FV - SRNE HF2430U80-H  |  ESP32-C3 + modulo RS485 auto-dir
  Lee registros Modbus RTU del inversor y los envia por Serial USB.

  Conexion:
    ESP32-C3          Modulo RS485
    GPIO6 (TX)   ---  TX
    GPIO7 (RX)   ---  RX
    3.3V              VCC
    GND               GND
    A --- RJ45 pin 7 (RS485-A)
    B --- RJ45 pin 8 (RS485-B)
*/

#include <Arduino.h>

#define PIN_TX      6
#define PIN_RX      7

#define MB_SLAVE    1
#define MB_BAUD     9600
#define MB_TIMEOUT  100

struct RegInfo {
  uint16_t addr;
  const char* name;
  float factor;
  bool is_signed;
};

static const RegInfo REGS[] = {
  {0x0100, "SOC",       1.0,   false},
  {0x0101, "Vbat",      0.1,   false},
  {0x0102, "Ibat",      0.1,   true},
  {0x0107, "PV1_V",     0.1,   false},
  {0x0108, "PV1_I",     0.1,   false},
  {0x0109, "PV1_P",     1.0,   false},
  {0x010A, "PV_P",      1.0,   false},
  {0x010B, "Carga",     1.0,   false},
  {0x010E, "Chg_P",     1.0,   false},
  {0x0210, "Estado",    1.0,   false},
  {0x0213, "Grid_V",    0.1,   false},
  {0x0214, "Grid_I",    0.1,   false},
  {0x0215, "Grid_Hz",   0.01,  false},
  {0x0216, "Inv_V",     0.1,   false},
  {0x0217, "Inv_I",     0.1,   false},
  {0x0218, "Inv_Hz",    0.01,  false},
  {0x0219, "Load_I",    0.1,   false},
  {0x021B, "Load_P",    1.0,   false},
  {0x021C, "Load_VA",   1.0,   false},
  {0x0220, "T_DCDC",    0.1,   true},
  {0x0221, "T_DCAC",    0.1,   true},
  {0x0222, "T_Trafo",   0.1,   true},
  {0x0223, "T_Amb",     0.1,   true},
  {0xF02F, "PV_hoy",    0.1,   false},
  {0xF030, "Load_hoy",  0.1,   false},
};

static const int N_REGS = sizeof(REGS) / sizeof(REGS[0]);

// CRC16 Modbus
static uint16_t crc16_modbus(const uint8_t* data, size_t len) {
  uint16_t crc = 0xFFFF;
  for (size_t i = 0; i < len; i++) {
    crc ^= data[i];
    for (int b = 0; b < 8; b++) {
      if (crc & 1) crc = (crc >> 1) ^ 0xA001;
      else         crc >>= 1;
    }
  }
  return crc;
}

// Lectura de 1 holding register via Modbus RTU
static bool read_holding_reg(uint16_t addr, uint16_t* value) {
  uint8_t req[8];
  req[0] = MB_SLAVE;             // Direccion esclavo
  req[1] = 0x03;                 // Funcion: Read Holding Registers
  req[2] = addr >> 8;            // Direccion del registro (high byte)
  req[3] = addr & 0xFF;          // (low byte)
  req[4] = 0x00;                 // Cantidad (high byte)
  req[5] = 0x01;                 // Cantidad: 1 registro
  uint16_t crc = crc16_modbus(req, 6);
  req[6] = crc & 0xFF;           // CRC (low byte)
  req[7] = crc >> 8;             // CRC (high byte)

  Serial1.write(req, 8);         // Enviar trama
  Serial1.flush();

  // Esperar respuesta
  unsigned long t0 = millis();
  size_t idx = 0;
  uint8_t resp[32];

  while (millis() - t0 < MB_TIMEOUT) {
    if (Serial1.available()) {
      resp[idx++] = Serial1.read();
      if (idx >= 3 && idx == (size_t)(resp[2] + 5)) break;
    }
  }

  // Validar respuesta
  if (idx < 5) return false;                      // Sin respuesta
  if (resp[0] != MB_SLAVE) return false;           // Direccion incorrecta
  if (resp[1] != 0x03) return false;               // Funcion incorrecta

  uint16_t rx_crc = resp[idx-2] | (resp[idx-1] << 8);
  if (crc16_modbus(resp, idx-2) != rx_crc) return false;  // CRC malo

  *value = (resp[3] << 8) | resp[4];              // Valor leido
  return true;
}

void setup() {
  Serial.begin(115200);                            // USB Serial (PC)
  delay(500);
  Serial1.begin(MB_BAUD, SERIAL_8N1, PIN_RX, PIN_TX);  // RS485 (inversor)
  Serial.println("{\"t\":\"init\",\"msg\":\"ADA-FV\"}");
}

void loop() {
  Serial.print("{\"t\":\"data\",\"ms\":");
  Serial.print(millis());
  Serial.print(",\"samples\":{");

  bool first = true;
  for (int i = 0; i < N_REGS; i++) {
    uint16_t raw = 0;
    bool ok = read_holding_reg(REGS[i].addr, &raw);

    if (!first) Serial.print(",");
    first = false;

    Serial.print("\"");
    Serial.print(REGS[i].name);
    Serial.print("\":");

    if (!ok) {
      Serial.print("null");
    } else {
      float val = REGS[i].is_signed
        ? (float)(int16_t)raw * REGS[i].factor
        : (float)raw * REGS[i].factor;
      Serial.print(val, 2);
    }
  }

  Serial.println("}}");
  delay(200);  // ~5 lecturas/segundo
}
```

### Compilacion y subida

1. Arduino IDE → Tools → Board → **ESP32-C3 Dev Module**
2. Tools → Port → seleccionar ESP32-C3
3. Abrir `esp32c3_srne_modbus.ino`, click Upload

---

## 5. Mapa Completo de Registros Modbus

Mapa completo extraido del protocolo SRNE MODBUS V2.08, verificado con inversor real (protocolo V1.07 detectado).

### Parametros de comunicacion

| Parametro | Valor |
|-----------|-------|
| Baud rate | 9600 |
| Data bits | 8 |
| Parity | None |
| Stop bits | 1 |
| Addr. default | 0x01 |
| Max registros/lectura | 32 |

### P00 — Product Info (0x000A–0x0049)

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

### P01 — DC Data (0x0100–0x0139)

| Dir | Nombre | Acceso | Unidad | Factor | Tipo |
|-----|--------|--------|--------|--------|------|
| 0x0100 | BatSoc | R | % | 1 | U_WORD |
| 0x0101 | BatVolt | R | V | 0.1 | U_WORD |
| 0x0102 | ChargeCurr | R | A | 0.1 | S_WORD |
| 0x0103 | DeviceBatTemper | R | C | 0.1 | S_WORD |
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
| 0x0114 | BatBmsTemp | R | C | 0.1 | S_WORD |
| 0x0115 | BatBmsChgLimitVolt | R | V | 0.1 | U_WORD |
| 0x0116 | BatBmsChgLimitCurr | R | A | 0.1 | U_WORD |
| 0x0117 | BatBmsDchgLimitCurr | R | A | 0.1 | U_WORD |
| 0x0118 | BmsAlarmH | R | - | 1 | U_WORD |
| 0x0119 | BmsAlarmL | R | - | 1 | U_WORD |
| 0x011A | BmsProtectH | R | - | 1 | U_WORD |
| 0x011B | BmsProtectL | R | - | 1 | U_WORD |
| 0x011C | Batt2Volt | R | V | 0.1 | U_WORD |
| 0x011D | Batt2Curr | R | A | 0.1 | S_WORD |
| 0x011E | Pv3Volt | R | V | 0.1 | U_WORD |
| 0x011F | Pv3Curr | R | A | 0.1 | U_WORD |
| 0x0120 | Pv3Power | R | W | 1 | U_WORD |
| 0x0121 | Pv4Volt | R | V | 0.1 | U_WORD |
| 0x0122 | Pv4Curr | R | A | 0.1 | U_WORD |
| 0x0123 | Pv4Power | R | W | 1 | U_WORD |
| 0x0124 | Pv5Volt | R | V | 0.1 | U_WORD |
| 0x0125 | Pv5Curr | R | A | 0.1 | U_WORD |
| 0x0126 | Pv5Power | R | W | 1 | U_WORD |
| 0x0127 | Pv6Volt | R | V | 0.1 | U_WORD |
| 0x0128 | Pv6Curr | R | A | 0.1 | U_WORD |
| 0x0129 | Pv6Power | R | W | 1 | U_WORD |
| 0x012F | BmsSwVer | R | - | 1 | U_WORD |
| 0x0130 | BmsHwVer | R | - | 1 | U_WORD |

### P02 — Inverter Data (0x0200–0x0263)

| Dir | Nombre | Acceso | Unidad | Factor | Tipo |
|-----|--------|--------|--------|--------|------|
| 0x0200 | CurrErrReg_0 | R | - | 1 | U_WORD |
| 0x0201 | CurrErrReg_1 | R | - | 1 | U_WORD |
| 0x0202 | CurrErrReg_2 | R | - | 1 | U_WORD |
| 0x0203 | CurrErrReg_3 | R | - | 1 | U_WORD |
| 0x0204 | CurrFcode_0 | R | - | 1 | U_WORD |
| 0x0205 | CurrFcode_1 | R | - | 1 | U_WORD |
| 0x0206 | CurrFcode_2 | R | - | 1 | U_WORD |
| 0x0207 | CurrFcode_3 | R | - | 1 | U_WORD |
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
| 0x0220 | Tempera (DC-DC) | R | C | 0.1 | S_WORD |
| 0x0221 | Temperb (DC-AC) | R | C | 0.1 | S_WORD |
| 0x0222 | Temperc (Transformer) | R | C | 0.1 | S_WORD |
| 0x0223 | Temperd (Ambient) | R | C | 0.1 | S_WORD |
| 0x0224 | Ibuck1 (PV charge curr) | R | A | 0.1 | U_WORD |
| 0x0225 | ParallCurrRms | R | A | 0.1 | U_WORD |
| 0x0228 | PBusVolt | R | V | 0.1 | U_WORD |
| 0x0229 | NBusVolt | R | V | 0.1 | U_WORD |
| 0x022A | GridVoltB | R | V | 0.1 | U_WORD |
| 0x022B | GridVoltC | R | V | 0.1 | U_WORD |
| 0x022C | InvVoltB | R | V | 0.1 | U_WORD |
| 0x022D | InvVoltC | R | V | 0.1 | U_WORD |
| 0x022E | InvCurrB | R | A | 0.1 | U_WORD |
| 0x022F | InvCurrC | R | A | 0.1 | U_WORD |
| 0x0230 | LoadCurrB | R | A | 0.1 | U_WORD |
| 0x0231 | LoadCurrC | R | A | 0.1 | U_WORD |
| 0x0232 | LoadActivePowerB | R | W | 1 | U_WORD |
| 0x0233 | LoadActivePowerC | R | W | 1 | U_WORD |
| 0x0236 | LoadRatioB | R | % | 1 | U_WORD |
| 0x0237 | LoadRatioC | R | % | 1 | U_WORD |
| 0x0238 | GridCurrB | R | A | 0.1 | U_WORD |
| 0x0239 | GridCurrC | R | A | 0.1 | U_WORD |
| 0x023A | GridActivePowerA | R | W | 1 | S_WORD |
| 0x023B | GridActivePowerB | R | W | 1 | S_WORD |
| 0x023C | GridActivePowerC | R | W | 1 | S_WORD |
| 0x023D | GridApparentPowerA | R | VA | 1 | U_WORD |
| 0x023E | GridApparentPowerB | R | VA | 1 | U_WORD |
| 0x023F | GridApparentPowerC | R | VA | 1 | U_WORD |
| 0x0240 | HomeLoadActivePowerA | R | W | 1 | U_WORD |
| 0x0241 | HomeLoadActivePowerB | R | W | 1 | U_WORD |
| 0x0242 | HomeLoadActivePowerC | R | W | 1 | U_WORD |
| 0x0243-0x0263 | Extensiones (GenPort, CT, etc.) | R | V/A/W | 0.1 | U_DWORD |

### P09 — Power Statistics (0xF000–0xF060)

| Dir | Nombre | Acceso | Unidad | Factor | Tipo |
|-----|--------|--------|--------|--------|------|
| 0xF000 | PVEnergyDay1 | R | kWh | 0.1 | U_WORD |
| 0xF001 | PVEnergyDay2 | R | kWh | 0.1 | U_WORD |
| 0xF002 | PVEnergyDay3 | R | kWh | 0.1 | U_WORD |
| 0xF003 | PVEnergyDay4 | R | kWh | 0.1 | U_WORD |
| 0xF004 | PVEnergyDay5 | R | kWh | 0.1 | U_WORD |
| 0xF005 | PVEnergyDay6 | R | kWh | 0.1 | U_WORD |
| 0xF006 | PVEnergyDay7 | R | kWh | 0.1 | U_WORD |
| 0xF007 | BatChgEnergyDay1-7 (7 regs) | R | Ah | 1 | U_WORD |
| 0xF00E | BatDisChgEnergyDay1-7 (7) | R | Ah | 1 | U_WORD |
| 0xF015 | LineChgEnergyDay1-7 (7) | R | Ah | 1 | U_WORD |
| 0xF01C | LoadConsumDay1-7 (7) | R | kWh | 0.1 | U_WORD |
| 0xF023 | LoadConsumFromLineDay1-7 (7) | R | kWh | 0.1 | U_WORD |
| 0xF02A | EnergyStatisticsDay_L | R | kWh | 0.1 | U_DWORD |
| 0xF02B | EnergyStatisticsDay_H | R | kWh | 0.1 | U_DWORD |
| 0xF02C | GeneratEnergyToGridToday | R | kWh | 0.1 | U_WORD |
| 0xF02D | BatChgAHToday | R | Ah | 1 | U_WORD |
| 0xF02E | BatDischgAHToday | R | Ah | 1 | U_WORD |
| 0xF02F | GeneratEnergyToday | R | kWh | 0.1 | U_WORD |
| 0xF030 | UsedEnergyToday | R | kWh | 0.1 | U_WORD |
| 0xF031 | WorkDaysTotal | R | day | 1 | U_WORD |
| 0xF032 | GridEnergyTotal_L | R | kWh | 0.1 | U_DWORD |
| 0xF033 | GridEnergyTotal_H | R | kWh | 0.1 | U_DWORD |
| 0xF034 | BatChgAHTotal_L | R | Ah | 1 | U_DWORD |
| 0xF035 | BatChgAHTotal_H | R | Ah | 1 | U_DWORD |
| 0xF036 | BatDischgAHTotal_L | R | Ah | 1 | U_DWORD |
| 0xF037 | BatDischgAHTotal_H | R | Ah | 1 | U_DWORD |
| 0xF038 | GeneratEnergyTotal_L | R | kWh | 0.1 | U_DWORD |
| 0xF039 | GeneratEnergyTotal_H | R | kWh | 0.1 | U_DWORD |
| 0xF03A | UsedEnergyTotal_L | R | kWh | 0.1 | U_DWORD |
| 0xF03B | UsedEnergyTotal_H | R | kWh | 0.1 | U_DWORD |
| 0xF03C | LineChgEnergyTday | R | Ah | 1 | U_WORD |
| 0xF03D | LoadConsumLineTday | R | kWh | 0.1 | U_WORD |
| 0xF03E | InvWorkTimeToday | R | min | 1 | U_WORD |
| 0xF03F | LineWorkTimeToday | R | min | 1 | U_WORD |
| 0xF040 | PowerOnTime (3 regs) | R | - | - | U_WORD |
| 0xF043 | LastEquaChgTime (3 regs) | R | - | - | U_WORD |
| 0xF046 | LineChgEnergyTotal_L | R | Ah | 1 | U_DWORD |
| 0xF047 | LineChgEnergyTotal_H | R | Ah | 1 | U_DWORD |
| 0xF048 | LoadConsumLineTotal_L | R | kWh | 0.1 | U_DWORD |
| 0xF049 | LoadConsumLineTotal_H | R | kWh | 0.1 | U_DWORD |
| 0xF04A | InvWorkTimeTotal | R | h | 1 | U_WORD |
| 0xF04B | LineWorkTimeTotal | R | h | 1 | U_WORD |
| 0xF04C | LineChgKwHTday | R | kWh | 0.1 | U_WORD |
| 0xF04E | BatDischgkWhToday | R | kWh | 0.1 | U_WORD |
| 0xF050 | BatChgkWhTotal_L | R | kWh | 0.1 | U_DWORD |
| 0xF051 | BatChgkWhTotal_H | R | kWh | 0.1 | U_DWORD |
| 0xF052 | BatDischgkWhTotal_L | R | kWh | 0.1 | U_DWORD |
| 0xF053 | BatDischgkWhTotal_H | R | kWh | 0.1 | U_DWORD |
| 0xF054 | LineChgkWhTotal_L | R | kWh | 0.1 | U_DWORD |
| 0xF055 | LineChgkWhTotal_H | R | kWh | 0.1 | U_DWORD |
| 0xF056 | GenLoadConsumToday | R | kWh | 0.1 | U_WORD |
| 0xF057 | GenChgkWhToday | R | kWh | 0.1 | U_WORD |
| 0xF058 | GenLoadConsumTotal_L | R | kWh | 0.1 | U_DWORD |
| 0xF059 | GenLoadConsumTotal_H | R | kWh | 0.1 | U_DWORD |
| 0xF05A | GenChgkWhTotal_L | R | kWh | 0.1 | U_DWORD |
| 0xF05B | GenChgkWhTotal_H | R | kWh | 0.1 | U_DWORD |
| 0xF05C | GenWorkTimeToday | R | h | 1 | U_WORD |
| 0xF05D | GenWorkTimeTotal | R | h | 1 | U_WORD |
| 0xF05E | HomdLoadConsumTday | R | kWh | 0.1 | U_WORD |
| 0xF060 | HomdLoadConsumTotal (2) | R | kWh | 0.1 | U_DWORD |

### P10 — Fault Records (0xF800–0xFA11)

**Nota:** El formato depende de la version del protocolo.
- **V2.08+**: 32 registros de falla, cada uno ocupa 16 registros (F800-F9FF).
  Primer registro = codigo de falla, 3 siguientes = sello de tiempo (ano/mes, dia/hora, min/seg), 12 = datos capturados.
- **V2.04 y anteriores**: 8 codigos de falla simples en 0xF800-0xF807.

| Dir | Registro | Longitud | Descripcion |
|-----|----------|----------|-------------|
| 0xF800 | FaultRecord0 | 16 regs | Codigo falla + tiempo + 12 datos |
| 0xF810 | FaultRecord1 | 16 regs | |
| ... | (hasta 32 registros) | ... | |
| 0xF9F0 | FaultRecord31 | 16 regs | Ultimo registro |

### MachineState (0x0210)

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

### ChargeState (0x010B)

| Valor | Estado |
|-------|--------|
| 0 | Charge off |
| 1 | Quick charge |
| 2 | Constant voltage charge |
| 4 | Float charge |
| 6 | Li battery activate |
| 8 | Full |

---

## 6. Software PC — Scripts Python

### 6.1 `dashboardesp.py` — Dashboard curses en terminal

Lee JSON del ESP32 por serial y muestra en terminal (curses).

```python
#!/usr/bin/env python3
"""Dashboard ESP32 — lee JSON del ESP32-C3 por serial"""

import sys, time, json, curses, serial, serial.tools.list_ports
from datetime import datetime

FIELDS = [
    ("SOC",       "SOC",        "%",     1,   False, 0),
    ("Vbat",      "Vbat",       "V",     1,   False, 1),
    ("Ibat",      "Ibat",       "A",     1,   True,  1),
    ("PV1_V",     "PV1 V",      "V",     1,   False, 1),
    ("PV1_I",     "PV1 I",      "A",     1,   False, 1),
    ("PV1_P",     "PV1 P",      "W",     1,   False, 0),
    ("PV_P",      "PV total P", "W",     1,   False, 0),
    ("Carga",     "Carga",      "",      1,   False, 0),
    ("Chg_P",     "Charge P",   "W",     1,   False, 0),
    ("Estado",    "Estado",     "",      1,   False, 0),
    ("Grid_V",    "Grid V",     "V",     1,   False, 1),
    ("Grid_I",    "Grid I",     "A",     1,   False, 1),
    ("Grid_Hz",   "Grid Hz",    "Hz",    1,   False, 2),
    ("Inv_V",     "Inv V",      "V",     1,   False, 1),
    ("Inv_I",     "Inv I",      "A",     1,   False, 1),
    ("Inv_Hz",    "Inv Hz",     "Hz",    1,   False, 2),
    ("Load_I",    "Load I",     "A",     1,   False, 1),
    ("Load_P",    "Load P",     "W",     1,   False, 0),
    ("Load_VA",   "Load VA",    "VA",    1,   False, 0),
    ("T_DCDC",    "T DC-DC",    "C",     1,   True,  1),
    ("T_DCAC",    "T DC-AC",    "C",     1,   True,  1),
    ("T_Trafo",   "T Trafo",    "C",     1,   True,  1),
    ("T_Amb",     "T Amb",      "C",     1,   True,  1),
    ("PV_hoy",    "PV hoy",     "kWh",   1,   False, 1),
    ("Load_hoy",  "Load hoy",   "kWh",   1,   False, 1),
]

KEYNAME = {f[0]: f[1] for f in FIELDS}
KEYUNIT = {f[0]: f[2] for f in FIELDS}
KEYDEC  = {f[0]: f[5] for f in FIELDS}

ESTADOS = {0:"Power-on",1:"Standby",2:"Init",3:"SoftStart",4:"AC op",
           5:"Inverter op",6:"Inv->AC",7:"AC->Inv",8:"Bat activ",9:"Off",10:"Fault"}
CARGAS  = {0:"Off",1:"Quick",2:"ConstV",4:"Float",6:"Li activ",8:"Full"}

def formatear(key, raw):
    if raw is None:
        return f"{KEYNAME[key]:>10s}: ---"
    dec = KEYDEC.get(key, 1)
    v = float(raw)
    fmt = f"{KEYNAME[key]:>10s}: {v:.{dec}f} {KEYUNIT.get(key,'')}"
    if key == "Estado" and raw in ESTADOS: fmt += f"  ({ESTADOS[int(raw)]})"
    if key == "Carga" and raw in CARGAS:  fmt += f"  ({CARGAS[int(raw)]})"
    if key == "Ibat" and raw is not None:
        sentido = "Desc" if float(raw) > 0 else "Carga"
        fmt += f" ({sentido})"
    return fmt

def detect_port():
    for p in serial.tools.list_ports.comports():
        if any(kw in p.description.lower() for kw in ["usb","serial","ch340","cp210","ftdi","uart"]):
            return p.device
    for p in serial.tools.list_ports.comports():
        return p.device
    return None

def dashboard(stdscr, port):
    curses.curs_set(0)
    curses.use_default_colors()
    stdscr.nodelay(1)
    stdscr.timeout(2000)

    ser = serial.Serial(port, 115200, timeout=5)
    ser.reset_input_buffer()

    samples = {}
    blink = False
    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        new_data = False
        for _ in range(5):
            try:
                line = ser.readline().decode(errors="replace").strip()
                if not line: continue
                data = json.loads(line)
                if data.get("t") == "data":
                    samples = data.get("samples", {})
                    new_data = True
            except: pass

        if new_data: blink = not blink
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        F = curses.A_BOLD
        led = "[X]" if blink else "[ ]"
        stdscr.addstr(0, 0, "=" * min(w-1, 70), F)
        stdscr.addstr(1, 0, f"  {led}  ADA-FV - SRNE HF2430U80-H    {now}", F)
        stdscr.addstr(2, 0, f"  Puerto: {port}  |  via ESP32-C3", F)
        stdscr.addstr(3, 0, "=" * min(w-1, 70), F)

        grupos = [
            ("PANEL SOLAR",   ["PV1_V","PV1_I","PV1_P","PV_P"]),
            ("BATERIA",       ["SOC","Vbat","Ibat","Carga"]),
            ("CARGA AC",      ["Inv_V","Inv_I","Load_I","Load_P","Load_VA"]),
            ("RED",           ["Grid_V","Grid_I","Grid_Hz"]),
            ("TEMPERATURAS",  ["T_DCDC","T_DCAC","T_Trafo","T_Amb"]),
            ("ESTADO",        ["Estado"]),
            ("ENERGIA HOY",   ["PV_hoy","Load_hoy"]),
        ]

        line = 5
        for titulo, keys in grupos:
            if line >= h-2: break
            stdscr.addstr(line, 0, f"-- {titulo} --", F)
            line += 1
            for key in keys:
                if line >= h-2: break
                txt = formatear(key, samples.get(key))
                stdscr.addstr(line, 0, txt)
                line += 1
            line += 1

        if line < h-1:
            stdscr.addstr(line, 0, "=" * min(w-1, 70))
            stdscr.addstr(line+1, 0, "  Q=salir  |  actualiza cada ~500ms")
        stdscr.refresh()

        for _ in range(20):
            k = stdscr.getch()
            if k in (ord('q'), ord('Q')):
                ser.close(); return
            time.sleep(0.1)

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else detect_port()
    if not port:
        print("ERROR: No se detecto puerto.")
        sys.exit(1)
    curses.wrapper(dashboard, port)

if __name__ == "__main__":
    main()
```

**Uso:**
```bash
python3 dashboardesp.py                  # auto-detect puerto
python3 dashboardesp.py /dev/ttyUSB0     # puerto explicito
```

### 6.2 `serverweb_srne.py` — Servidor web local

Lee JSON del ESP32 por serial y sirve pagina web en `http://localhost:8080`.

```python
#!/usr/bin/env python3
import sys, json, threading, serial, serial.tools.list_ports
from http.server import HTTPServer, BaseHTTPRequestHandler

latest_json = "{}"
port = None

def detect_port():
    for p in serial.tools.list_ports.comports():
        if any(kw in p.description.lower() for kw in ["usb","serial","ch340","cp210","ftdi","uart"]):
            return p.device
    for p in serial.tools.list_ports.comports(): return p.device
    return None

def reader_thread():
    global latest_json
    ser = serial.Serial(port, 115200, timeout=5)
    ser.reset_input_buffer()
    while True:
        line = ser.readline().decode(errors="replace").strip()
        if not line: continue
        data = json.loads(line)
        if data.get("t") == "data": latest_json = line

HTML = """<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ADA-FV - SRNE HF2430U80-H</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:#fff;color:#000;font-family:Arial,sans-serif;padding:30px}
  h1{font-size:3em} #hora{font-size:1.8em;margin:10px 0 25px;color:#333}
  .g{display:inline-block;vertical-align:top;margin:10px 30px 10px 0;min-width:250px}
  .gt{font-size:1.6em;font-weight:bold;border-bottom:3px solid #000;margin-bottom:10px;padding-bottom:5px}
  .r{font-size:1.8em;padding:6px 0} .rn{color:#555} .rv{font-weight:bold}
  #led{display:inline-block;width:20px;height:20px;border-radius:50%;margin-right:12px}
  .on{background:#00cc00} .off{background:#ddd}
</style></head><body>
<div style="display:flex;align-items:center;gap:10px"><div id="led" class="off"></div><h1>ADA-FV - SRNE HF2430U80-H</h1></div>
<div id="hora">conectando...</div><div id="datos"></div>
<script>
const g=[['PANEL SOLAR',['PV1_V','PV1_I','PV1_P','PV_P']],['BATERIA',['SOC','Vbat','Ibat','Carga']],['CARGA AC',['Inv_V','Inv_I','Load_I','Load_P','Load_VA']],['RED',['Grid_V','Grid_I','Grid_Hz']],['TEMP',['T_DCDC','T_DCAC','T_Trafo','T_Amb']],['ESTADO',['Estado']],['ENERGIA',['PV_hoy','Load_hoy']]];
const n={'SOC':'SOC','Vbat':'Vbat','Ibat':'Ibat','PV1_V':'PV1 V','PV1_I':'PV1 I','PV1_P':'PV1 P','PV_P':'PV tot','Carga':'Carga','Estado':'Estado','Grid_V':'Red V','Grid_I':'Red I','Grid_Hz':'Red Hz','Inv_V':'Inv V','Inv_I':'Inv I','Inv_Hz':'Inv Hz','Load_I':'Load I','Load_P':'Load P','Load_VA':'Load VA','T_DCDC':'DC-DC','T_DCAC':'DC-AC','T_Trafo':'Trafo','T_Amb':'Amb','PV_hoy':'PV hoy','Load_hoy':'Load hoy'};
const u={'SOC':'%','Vbat':'V','Ibat':'A','PV1_V':'V','PV1_I':'A','PV1_P':'W','PV_P':'W','Carga':'','Estado':'','Grid_V':'V','Grid_I':'A','Grid_Hz':'Hz','Inv_V':'V','Inv_I':'A','Inv_Hz':'Hz','Load_I':'A','Load_P':'W','Load_VA':'VA','T_DCDC':'C','T_DCAC':'C','T_Trafo':'C','T_Amb':'C','PV_hoy':'kWh','Load_hoy':'kWh'};
const e={0:'Power-on',1:'Standby',2:'Init',3:'SoftStart',4:'AC op',5:'Inv op',6:'Inv->AC',7:'AC->Inv',8:'Bat activ',9:'Off',10:'Fault'};
const c={0:'Off',1:'Quick',2:'ConstV',4:'Float',6:'Li activ',8:'Full'};
async function f(){try{
  const r=await fetch('/api');const d=await r.json();if(d.t!='data')return;
  const s=d.samples;document.getElementById('led').className='on';
  setTimeout(()=>document.getElementById('led').className='off',200);
  document.getElementById('hora').textContent=new Date().toLocaleTimeString()+' | ms='+d.ms;
  let h='';for(const[t,ks]of g){h+='<div class="g"><div class="gt">'+t+'</div>';
  for(const k of ks){let v=s[k];let x=v!==null&&v!==undefined?v:'---';let x2='';
  if(k=='Estado'&&v!==null&&v in e)x2=' '+e[v];if(k=='Carga'&&v!==null&&v in c)x2=' '+c[v];
  if(k=='Ibat'&&v!==null)x2=v>0?' (DESC)':' (CARG)';
  h+='<div class="r"><span class="rn">'+(n[k]||k)+':</span> <span class="rv">'+x+'</span> '+(u[k]||'')+x2+'</div>';}
  h+='</div>';}document.getElementById('datos').innerHTML=h;
}catch(e){}}
setInterval(f,2000);f();
</script></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api":
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(latest_json.encode())
        else:
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML.encode())
    def log_message(self,*a): pass

def main():
    global port
    port = sys.argv[1] if len(sys.argv) > 1 else detect_port()
    if not port: print("ERROR: No se detecto puerto."); sys.exit(1)
    threading.Thread(target=reader_thread, daemon=True).start()
    print(f"Servidor en http://localhost:8080")
    print(f"Datos desde {port}")
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()

if __name__ == "__main__": main()
```

**Uso:**
```bash
python3 serverweb_srne.py              # auto-detect
python3 serverweb_srne.py /dev/ttyUSB0 # puerto explicito
# Abrir http://localhost:8080 en el navegador
```

### 6.3 `reader_srne.py` — Lector serial con log CSV

```bash
python3 reader_srne.py                  # muestra en pantalla
python3 reader_srne.py --log            # guarda a archivo CSV
python3 reader_srne.py --csv            # output CSV en pantalla
```

### 6.4 `test_modbus_srne.py` — Prueba de comunicacion Modbus

Lee ~150 registros del inversor (Modbus directo desde PC, sin ESP32).

```bash
python3 test_modbus_srne.py                     # lectura unica
python3 test_modbus_srne.py /dev/ttyUSB0 --loop # modo continuo
```

---

## 7. Resultados de Prueba (28-Jul-2026)

Datos reales obtenidos durante prueba de conexion con PC via USB-RS485 (Qinheng CH340):

| Variable        | Valor  | Unidad |
|----------------|--------|--------|
| SOC            | 100    | %      |
| Vbat           | 27.9   | V      |
| Ibat           | -5.0   | A (carga) |
| PV1_V          | 129.5  | V      |
| PV1_I          | 1.0    | A      |
| PV1_P          | 129    | W      |
| Load_P         | 165    | W      |
| Load_VA        | 191    | VA     |
| T_DC-DC        | 41.7   | C      |
| T_DC-AC        | 35.2   | C      |
| T_Trafo        | 37.8   | C      |
| T_Amb          | 36.2   | C      |
| PV_hoy         | 0.0    | kWh    |
| Load_hoy       | 0.8    | kWh    |
| PV_total       | 811.7  | kWh    |
| Load_total     | 711.3  | kWh    |
| Protocolo      | V1.07  | -      |

---

## 8. Guia Rapida de Uso

### Con ESP32-C3 conectado al inversor:

```bash
# 1. Terminal dashboard (recomendado)
python3 dashboardesp.py

# 2. Servidor web (abrir http://localhost:8080)
python3 serverweb_srne.py

# 3. Log CSV
python3 reader_srne.py --log

# 4. Debug (ver JSON crudo)
python3 debug_serial.py
```

### Sin ESP32 (Modbus directo desde PC con USB-RS485):

```bash
python3 test_modbus_srne.py                # lectura completa
python3 test_modbus_srne.py --loop         # monitor continuo
python3 dashboard_srne.py                  # dashboard curses
```

---

## 9. Cableado Resumen

| ESP32-C3 | Modulo RS485 | Inversor (RJ45) |
|----------|-------------|-----------------|
| GPIO6    | TX          | -               |
| GPIO7    | RX          | -               |
| 3.3V     | VCC         | -               |
| GND      | GND         | -               |
| -        | A           | Pin 7           |
| -        | B           | Pin 8           |

Pinout RJ45 del inversor SRNE HF2430U80-H:
- Pin 1-6: no conectar
- **Pin 7: RS485-A (blanco/naranja)**
- **Pin 8: RS485-B (naranja)**

---
