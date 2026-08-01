# Manual Tecnico — ADA-FV

Sistema de monitorizacion para inversor SRNE HF2430U80-H vía ESP32-C3 + RS485.
Proyecto de grado ADA-FV (Arquitectura de Datos para Aulas Fotovoltaicas) — Aulas Abiertas Sostenibles, Universidad del Magdalena.

---

## 1. Estructura del Proyecto

```
Proyecto_ADA-FV/
├── README.md                        ← Portada del repositorio
├── 00_DOCUMENTACION_PRINCIPAL/      ← Manual técnico (anteproyecto/informe cuando existan)
│   └── Manual_Tecnico_ADA-FV.md     ← MANUAL COMPLETO (este documento)
├── 01_INVESTIGACION_Y_BASE_CONOCIMIENTO/
│   ├── Datasheets/
│   │   ├── Baterias/                ← Green Point 25.6V 200AH
│   │   └── Inversores/              ← SRNE HF2430U80-H
│   ├── Notas_Tecnicas/
│   │   ├── Protocolo_Modbus_SRNE.md
│   │   ├── Proyectos_Referencia_Modbus_Inversores.md
│   │   ├── SRNE_Modbus_Entities.md
│   │   └── SRNE_Modbus_Register_Map.md  ← Mapa completo de registros
│   └── Referencias_Bibliograficas/
├── 03_FIRMWARE/
│   └── ada_fv/
│       ├── esp32c3_srne_modbus.ino  ← FIRMWARE PRINCIPAL (ESP32-C3)
│       ├── platformio.ini
│       ├── README.md
│       └── esphome_reference/       ← Modulos YAML de referencia
├── 04_SOFTWARE_PC/
│   ├── README.md
│   ├── test_modbus_srne.py          ← Prueba de comunicacion Modbus (lectura completa)
│   ├── dashboard_srne.py            ← Dashboard curses (Modbus directo desde PC)
│   ├── dashboardesp.py              ← Dashboard curses (lee JSON del ESP32 por serial)
│   ├── reader_srne.py               ← Lector serial JSON + log CSV
│   └── debug_serial.py              ← Debug: muestra raw del serial
└── 05_MEDICIONES_Y_ENSAYOS/         ← Dumps Modbus reales de validacion
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
  ============================================================================
  ADA-FV — SRNE HF2430U80-H
  Firmware para ESP32-C3 + modulo RS485 (auto-direccion)

  PROPOSITO:
    Leer los registros Modbus RTU del inversor solar SRNE HF2430U80-H y
    reenviar los valores (ya escalados) como JSON por el USB Serial hacia
    una PC, donde un script Python los muestra o guarda.

  TOPOLOGIA DE COMUNICACION:
    Inversor (esclavo Modbus, addr 0x01, 9600 8N1)
        |
        | RS485 — RJ45 pin 7 (A), pin 8 (B)
        |
    Modulo RS485 (TX/RX/VCC/GND) — auto-direccion, no requiere DE/RE
        |
    ESP32-C3
        |-- GPIO6 = TX1  --> modulo TX
        |-- GPIO7 = RX1  --> modulo RX
        |-- 3.3V  --> VCC
        |-- GND   --> GND
        |
        | USB-UART a 115200 baud
        v
    PC (dashboardesp.py / reader_srne.py)

  FORMATO DE SALIDA (USB Serial, 115200 baud):
    {"t":"data","ms":1234,"samples":{"SOC":100,"Vbat":27.9,...}}

  NOTA SOBRE EL MODULO RS485 AUTO-DIR:
    Estos modulos conmutan automaticamente entre TX y RX segun la
    actividad del bus. Por eso NO se necesita un pin GPIO de control
    (DE/RE). Solo se conectan TX, RX, VCC y GND.
  ============================================================================
*/

#include <Arduino.h>

// ============================================================================
// DEFINICION DE PINES
// ============================================================================
#define PIN_TX      6   // GPIO6  -> TX del modulo RS485 (Serial1 TX)
#define PIN_RX      7   // GPIO7  -> RX del modulo RS485 (Serial1 RX)

// ============================================================================
// PARAMETROS MODBUS
// ============================================================================
#define MB_SLAVE    1   // Direccion Modbus del inversor (default 0x01)
#define MB_BAUD     9600 // Baud rate del bus RS485 del inversor
#define MB_TIMEOUT  100  // Tiempo maximo (ms) de espera de respuesta del inversor

// ============================================================================
// TABLA DE REGISTROS A LEER
// ============================================================================
// Cada entrada define:
//   addr      : direccion Modbus (hex) del holding register
//   name      : nombre clave con el que sale en el JSON
//   factor    : multiplicador para convertir el valor crudo a unidad real
//   is_signed : true si el registro es con signo (S_WORD, complemento a 2)
//
// Ejemplo: Vbat crudo = 279  ->  279 * 0.1 = 27.9 V
struct RegInfo {
  uint16_t addr;        // Direccion del registro
  const char* name;     // Nombre en el JSON de salida
  float factor;         // Factor de escala
  bool is_signed;       // Tipo signed/unsigned
};

// Tabla de los 25 registros mas importantes para el monitoreo
static const RegInfo REGS[] = {
  // --- Bateria (P01) ---
  {0x0100, "SOC",       1.0,   false},  // Estado de carga de la bateria [%]
  {0x0101, "Vbat",      0.1,   false},  // Voltaje de bateria [V]
  {0x0102, "Ibat",      0.1,   true},   // Corriente de bateria [A] (+descarga/-carga)
  // --- Panel solar (P01) ---
  {0x0107, "PV1_V",     0.1,   false},  // Voltaje del panel PV1 [V]
  {0x0108, "PV1_I",     0.1,   false},  // Corriente del panel PV1 [A]
  {0x0109, "PV1_P",     1.0,   false},  // Potencia del panel PV1 [W]
  {0x010A, "PV_P",      1.0,   false},  // Potencia total PV [W]
  {0x010B, "Carga",     1.0,   false},  // Estado de carga (codigo, ver tabla)
  {0x010E, "Chg_P",     1.0,   false},  // Potencia de carga de bateria [W]
  // --- Inversor (P02) ---
  {0x0210, "Estado",    1.0,   false},  // Estado de la maquina (codigo)
  {0x0213, "Grid_V",    0.1,   false},  // Voltaje de red [V]
  {0x0214, "Grid_I",    0.1,   false},  // Corriente de red [A]
  {0x0215, "Grid_Hz",   0.01,  false},  // Frecuencia de red [Hz]
  {0x0216, "Inv_V",     0.1,   false},  // Voltaje del inversor [V]
  {0x0217, "Inv_I",     0.1,   false},  // Corriente del inversor [A]
  {0x0218, "Inv_Hz",    0.01,  false},  // Frecuencia del inversor [Hz]
  {0x0219, "Load_I",    0.1,   false},  // Corriente de carga [A]
  {0x021B, "Load_P",    1.0,   false},  // Potencia activa de carga [W]
  {0x021C, "Load_VA",   1.0,   false},  // Potencia aparente de carga [VA]
  // --- Temperaturas (P02) ---
  {0x0220, "T_DCDC",    0.1,   true},   // Temp. del convertidor DC-DC [C]
  {0x0221, "T_DCAC",    0.1,   true},   // Temp. del convertidor DC-AC [C]
  {0x0222, "T_Trafo",   0.1,   true},   // Temp. del transformador [C]
  {0x0223, "T_Amb",     0.1,   true},   // Temp. ambiente [C]
  // --- Estadisticas de energia (P09) ---
  {0xF02F, "PV_hoy",    0.1,   false},  // Energia PV generada hoy [kWh]
  {0xF030, "Load_hoy",  0.1,   false},  // Energia consumida hoy [kWh]
};

// Numero de registros en la tabla (se calcula solo)
static const int N_REGS = sizeof(REGS) / sizeof(REGS[0]);

// ============================================================================
// CRC-16 MODBUS
// ============================================================================
// Calcula el CRC de 16 bits (polinomio 0xA001) usado por el protocolo Modbus
// RTU. El CRC viaja al final de cada trama, byte bajo primero.
//   data : apuntador a la trama
//   len  : cantidad de bytes de la trama (sin incluir el CRC)
static uint16_t crc16_modbus(const uint8_t* data, size_t len) {
  uint16_t crc = 0xFFFF;              // Valor inicial estandar
  for (size_t i = 0; i < len; i++) {  // Recorrer cada byte de la trama
    crc ^= data[i];                   // XOR con el byte actual
    for (int b = 0; b < 8; b++) {     // 8 desplazamientos por byte
      if (crc & 1) crc = (crc >> 1) ^ 0xA001;  // Si bit menos significativo=1
      else         crc >>= 1;                   // Si no, solo desplazar
    }
  }
  return crc;
}

// ============================================================================
// LECTURA DE 1 HOLDING REGISTER (Funcion Modbus 0x03)
// ============================================================================
// Envia la trama de lectura al inversor y espera la respuesta.
// Valida: direccion del esclavo, codigo de funcion y CRC.
//   addr  : direccion del registro a leer
//   value : puntero donde se devuelve el valor crudo de 16 bits
//   Retorna: true si la lectura fue exitosa, false si hubo error
static bool read_holding_reg(uint16_t addr, uint16_t* value) {
  uint8_t req[8];                     // Trama de peticion: 8 bytes
  req[0] = MB_SLAVE;                  // 1) Direccion del esclavo (0x01)
  req[1] = 0x03;                      // 2) Funcion: Read Holding Registers
  req[2] = addr >> 8;                 // 3) Direccion del registro (byte alto)
  req[3] = addr & 0xFF;               // 4) Direccion del registro (byte bajo)
  req[4] = 0x00;                      // 5) Cantidad de registros (byte alto)
  req[5] = 0x01;                      // 6) Cantidad de registros: 1
  uint16_t crc = crc16_modbus(req, 6);// Calcular CRC de los 6 primeros bytes
  req[6] = crc & 0xFF;                // 7) CRC (byte bajo)
  req[7] = crc >> 8;                  // 8) CRC (byte alto)

  Serial1.write(req, 8);              // Enviar la trama por el bus RS485
  Serial1.flush();                    // Asegurar que se transmita completa

  // Esperar la respuesta del inversor dentro del tiempo maximo (MB_TIMEOUT)
  unsigned long t0 = millis();        // Marca de tiempo de inicio
  size_t idx = 0;                     // Contador de bytes recibidos
  uint8_t resp[32];                   // Buffer de respuesta

  while (millis() - t0 < MB_TIMEOUT) {
    if (Serial1.available()) {        // Si llego un byte del inversor
      resp[idx++] = Serial1.read();   // Guardarlo en el buffer
      // Trama esperada: addr + func + bytecount + datos + CRC(2) = resp[2]+5
      if (idx >= 3 && idx == (size_t)(resp[2] + 5)) break;
    }
  }

  // --- Validaciones de la respuesta ---
  if (idx < 5) return false;          // Respuesta demasiado corta (sin datos)
  if (resp[0] != MB_SLAVE) return false;  // Direccion no coincide
  if (resp[1] != 0x03) return false;      // Funcion no coincide

  // Verificar CRC recibido contra el calculado
  uint16_t rx_crc = resp[idx-2] | (resp[idx-1] << 8);
  if (crc16_modbus(resp, idx-2) != rx_crc) return false;  // CRC invalido

  *value = (resp[3] << 8) | resp[4];  // Los 2 bytes de datos del registro
  return true;                        // Lectura exitosa
}

// ============================================================================
// CONFIGURACION INICIAL (setup)
// ============================================================================
void setup() {
  // Serial USB hacia la PC (para enviar el JSON) — 115200 baud
  Serial.begin(115200);
  delay(500);                         // Esperar a que la PC abra el puerto

  // Serial1 hacia el modulo RS485 / inversor — 9600 8N1 (estandar SRNE)
  Serial1.begin(MB_BAUD, SERIAL_8N1, PIN_RX, PIN_TX);

  // Avisar por USB que el firmware inicio correctamente
  Serial.println("{\"t\":\"init\",\"msg\":\"ADA-FV encendido\"}");
}

// ============================================================================
// BUCLE PRINCIPAL (loop)
// ============================================================================
// En cada ciclo lee TODOS los registros de la tabla y genera un JSON que
// envia por USB. Al final espera 200 ms (~5 lecturas por segundo).
void loop() {
  // Cabecera del JSON: tipo "data" y tiempo de ejecucion (millis)
  Serial.print("{\"t\":\"data\",\"ms\":");
  Serial.print(millis());
  Serial.print(",\"samples\":{");

  // Recorrer todos los registros definidos en la tabla REGS[]
  bool first = true;                  // Control para el separador de coma
  for (int i = 0; i < N_REGS; i++) {
    uint16_t raw = 0;                 // Valor crudo leido del inversor
    bool ok = read_holding_reg(REGS[i].addr, &raw);

    // Separador "," entre elementos del JSON (excepto el primero)
    if (!first) Serial.print(",");
    first = false;

    // Nombre del campo JSON
    Serial.print("\"");
    Serial.print(REGS[i].name);
    Serial.print("\":");

    if (!ok) {
      // No hubo respuesta del inversor: campo null
      Serial.print("null");
    } else {
      // Escalar el valor: si es signed se interpreta como int16 con signo
      float val = REGS[i].is_signed
        ? (float)(int16_t)raw * REGS[i].factor
        : (float)raw * REGS[i].factor;
      Serial.print(val, 2);           // Imprimir con 2 decimales
    }
  }

  Serial.println("}}");               // Cerrar JSON con salto de linea

  delay(200);                         // Pausa: ~5 ciclos de lectura por segundo
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
"""
============================================================================
Dashboard en terminal (curses) para ADA-FV — SRNE HF2430U80-H
============================================================================

PROPOSITO:
  Leer el JSON que envia el ESP32-C3 por USB Serial y mostrarlo en la
  terminal en tiempo real, organizado por grupos (panel, bateria, red, etc).

ARQUITECTURA:
  ESP32-C3 --(JSON por USB Serial)--> este script --> terminal curses

USO:
  python3 dashboardesp.py                  # auto-detecta el puerto
  python3 dashboardesp.py /dev/ttyUSB0     # puerto explicito

TECLAS:
  Q  -> salir del dashboard

NOTA:
  Este script NO habla Modbus. Solo lee el JSON que el ESP32-C3 ya
  proceso y envio escalado. Para hablar Modbus directo desde PC use
  dashboard_srne.py o test_modbus_srne.py.
============================================================================
"""

import sys          # Argumentos de linea de comandos
import time         # Pausas y temporizacion
import json         # Parsear el JSON que llega por serial
import curses       # Interfaz de terminal en tiempo real
import serial       # Comunicacion serial con el ESP32-C3
import serial.tools.list_ports  # Deteccion automatica de puertos
from datetime import datetime   # Marca de tiempo para la cabecera

# ============================================================================
# TABLA DE CAMPOS A MOSTRAR
# ============================================================================
# Cada entrada: (clave_json, nombre_visible, unidad, factor, signed, decimales)
# El factor SIEMPRE es 1 porque el ESP32-C3 ya escala los valores.
# El "signed" no se aplica: el ESP32 ya lo interpreto.
FIELDS = [
    ("SOC",       "SOC",        "%",     1,   False, 0),  # Estado de carga [%]
    ("Vbat",      "Vbat",       "V",     1,   False, 1),  # Voltaje bateria [V]
    ("Ibat",      "Ibat",       "A",     1,   True,  1),  # Corriente bateria [A]
    ("PV1_V",     "PV1 V",      "V",     1,   False, 1),  # Voltaje panel [V]
    ("PV1_I",     "PV1 I",      "A",     1,   False, 1),  # Corriente panel [A]
    ("PV1_P",     "PV1 P",      "W",     1,   False, 0),  # Potencia panel [W]
    ("PV_P",      "PV total P", "W",     1,   False, 0),  # Potencia PV total [W]
    ("Carga",     "Carga",      "",      1,   False, 0),  # Estado de carga (codigo)
    ("Chg_P",     "Charge P",   "W",     1,   False, 0),  # Potencia de carga [W]
    ("Estado",    "Estado",     "",      1,   False, 0),  # Estado de maquina
    ("Grid_V",    "Grid V",     "V",     1,   False, 1),  # Voltaje de red [V]
    ("Grid_I",    "Grid I",     "A",     1,   False, 1),  # Corriente de red [A]
    ("Grid_Hz",   "Grid Hz",    "Hz",    1,   False, 2),  # Frecuencia de red [Hz]
    ("Inv_V",     "Inv V",      "V",     1,   False, 1),  # Voltaje inversor [V]
    ("Inv_I",     "Inv I",      "A",     1,   False, 1),  # Corriente inversor [A]
    ("Inv_Hz",    "Inv Hz",     "Hz",    1,   False, 2),  # Frecuencia inversor [Hz]
    ("Load_I",    "Load I",     "A",     1,   False, 1),  # Corriente de carga [A]
    ("Load_P",    "Load P",     "W",     1,   False, 0),  # Potencia activa [W]
    ("Load_VA",   "Load VA",    "VA",    1,   False, 0),  # Potencia aparente [VA]
    ("T_DCDC",    "T DC-DC",    "C",     1,   True,  1),  # Temp. DC-DC [C]
    ("T_DCAC",    "T DC-AC",    "C",     1,   True,  1),  # Temp. DC-AC [C]
    ("T_Trafo",   "T Trafo",    "C",     1,   True,  1),  # Temp. trafo [C]
    ("T_Amb",     "T Amb",      "C",     1,   True,  1),  # Temp. ambiente [C]
    ("PV_hoy",    "PV hoy",     "kWh",   1,   False, 1),  # Energia PV de hoy [kWh]
    ("Load_hoy",  "Load hoy",   "kWh",   1,   False, 1),  # Energia consumida hoy [kWh]
]

# Diccionarios de acceso rapido por clave JSON
KEYNAME = {f[0]: f[1] for f in FIELDS}   # clave -> nombre visible
KEYUNIT = {f[0]: f[2] for f in FIELDS}   # clave -> unidad
KEYDEC  = {f[0]: f[5] for f in FIELDS}   # clave -> cantidad de decimales

# ============================================================================
# TABLAS DE DECODIFICACION DE CODIGOS
# ============================================================================
# Estado de la maquina (registro 0x0210 / campo "Estado")
ESTADOS = {0:"Power-on", 1:"Standby", 2:"Init", 3:"SoftStart",
           4:"AC op", 5:"Inverter op", 6:"Inv->AC", 7:"AC->Inv",
           8:"Bat activ", 9:"Manual off", 10:"Fault"}
# Estado de carga (registro 0x010B / campo "Carga")
CARGAS = {0:"Off", 1:"Quick", 2:"ConstV", 4:"Float", 6:"Li activ", 8:"Full"}

# ============================================================================
# FORMATEO DE UNA LINEA DEL DASHBOARD
# ============================================================================
def formatear(key, raw):
    """Convierte el valor crudo del JSON en texto listo para mostrar.

    Parametros:
        key : clave del campo en el JSON (ej: "Vbat")
        raw : valor numerico recibido (o None si el ESP32 no respondio)
    Retorna:
        string con el texto formateado, ej: "      Vbat: 27.9 V"
    """
    if raw is None:
        # El ESP32 no obtuvo respuesta del inversor para este campo
        return f"{KEYNAME[key]:>10s}: ---"

    dec = KEYDEC.get(key, 1)            # Decimales para este campo
    v = float(raw)                      # Valor ya escalado por el ESP32
    fmt = f"{KEYNAME[key]:>10s}: {v:.{dec}f} {KEYUNIT.get(key,'')}"

    # Anadir descripcion textual para los campos de codigo
    if key == "Estado" and raw in ESTADOS:
        fmt += f"  ({ESTADOS[int(raw)]})"
    if key == "Carga" and raw in CARGAS:
        fmt += f"  ({CARGAS[int(raw)]})"
    if key == "Ibat" and raw is not None:
        # Convencion SRNE: positivo = descarga, negativo = carga
        sentido = "Desc" if float(raw) > 0 else "Carga"
        fmt += f" ({sentido})"
    return fmt

# ============================================================================
# DETECCION AUTOMATICA DE PUERTO SERIAL
# ============================================================================
def detect_port():
    """Busca un puerto serial disponible (ESP32-C3 conectado por USB)."""
    # Primera pasada: preferir puertos con nombre sugerente
    for p in serial.tools.list_ports.comports():
        if any(kw in p.description.lower() for kw in ["usb","serial","ch340","cp210","ftdi","uart"]):
            return p.device
    # Segunda pasada: usar el primer puerto que exista
    for p in serial.tools.list_ports.comports():
        return p.device
    return None                        # No se encontro ningun puerto

# ============================================================================
# BUCLE PRINCIPAL DEL DASHBOARD (curses)
# ============================================================================
def dashboard(stdscr, port):
    """Dibuja el dashboard en tiempo real usando curses.

    Parametros:
        stdscr : objeto de pantalla que provee curses.wrapper
        port   : ruta del puerto serial (ej: /dev/ttyUSB0)
    """
    # --- Configuracion de curses ---
    curses.curs_set(0)                  # Ocultar el cursor
    curses.use_default_colors()         # Usar colores por defecto del terminal
    stdscr.nodelay(1)                   # getch() sin bloqueo
    stdscr.timeout(2000)                # Timeout de espera de teclado (2s)

    # --- Abrir el puerto serial hacia el ESP32-C3 ---
    try:
        ser = serial.Serial(port, 115200, timeout=5)  # 115200 baud
        ser.reset_input_buffer()        # Limpiar datos viejos del buffer
    except Exception as e:
        stdscr.addstr(0, 0, f"ERROR: {e}")
        stdscr.refresh()
        time.sleep(3)
        return

    samples = {}                        # Ultimo muestreo recibido (dict)
    blink = False                       # Estado del indicador [X] / [ ]

    while True:
        stdscr.erase()                  # Limpiar pantalla
        h, w = stdscr.getmaxyx()        # Tamano actual de la terminal

        # --- Leer lineas JSON del ESP32 (hasta 5 por refresco) ---
        new_data = False
        for _ in range(5):
            try:
                line = ser.readline().decode(errors="replace").strip()
                if not line: continue
                data = json.loads(line)         # Parsear el JSON
                if data.get("t") == "data":     # Solo tramas de datos
                    samples = data.get("samples", {})
                    new_data = True
            except: pass                        # Ignorar lineas corruptas

        # Parpadear el indicador si llego un dato nuevo
        if new_data:
            blink = not blink

        # Marca de tiempo de la cabecera
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # --- Cabecera ---
        F = curses.A_BOLD               # Atributo negrita
        led = "[X]" if blink else "[ ]" # Indicador de datos recibidos
        stdscr.addstr(0, 0, "=" * min(w-1, 70), F)
        stdscr.addstr(1, 0, f"  {led}  ADA-FV - SRNE HF2430U80-H    {now}", F)
        stdscr.addstr(2, 0, f"  Puerto: {port}  |  via ESP32-C3", F)
        stdscr.addstr(3, 0, "=" * min(w-1, 70), F)

        # --- Definicion de los grupos de datos a mostrar ---
        grupos = [
            ("PANEL SOLAR",   ["PV1_V","PV1_I","PV1_P","PV_P"]),
            ("BATERIA",       ["SOC","Vbat","Ibat","Carga"]),
            ("CARGA AC",      ["Inv_V","Inv_I","Load_I","Load_P","Load_VA"]),
            ("RED",           ["Grid_V","Grid_I","Grid_Hz"]),
            ("TEMPERATURAS",  ["T_DCDC","T_DCAC","T_Trafo","T_Amb"]),
            ("ESTADO",        ["Estado"]),
            ("ENERGIA HOY",   ["PV_hoy","Load_hoy"]),
        ]

        # --- Dibujar cada grupo y sus campos ---
        line = 5                        # Fila inicial (despues de la cabecera)
        for titulo, keys in grupos:
            if line >= h-2: break       # No salirse de la pantalla
            stdscr.addstr(line, 0, f"-- {titulo} --", F)
            line += 1
            for key in keys:
                if line >= h-2: break
                txt = formatear(key, samples.get(key))
                stdscr.addstr(line, 0, txt)
                line += 1
            line += 1                   # Fila en blanco entre grupos

        # --- Pie de pagina ---
        if line < h-1:
            stdscr.addstr(line, 0, "=" * min(w-1, 70))
            stdscr.addstr(line+1, 0, "  Q=salir  |  actualiza cada ~500ms")

        stdscr.refresh()                # Volcar cambios a la terminal

        # --- Esperar tecla Q para salir (20 x 100ms = 2s) ---
        for _ in range(20):
            k = stdscr.getch()
            if k in (ord('q'), ord('Q')):
                ser.close()             # Cerrar puerto serial
                return
            time.sleep(0.1)

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================
def main():
    """Punto de entrada: detecta el puerto y lanza el dashboard curses."""
    port = sys.argv[1] if len(sys.argv) > 1 else detect_port()
    if not port:
        print("ERROR: No se detecto puerto.")
        sys.exit(1)
    # curses.wrapper se encarga de inicializar/restaurar la terminal
    curses.wrapper(dashboard, port)

if __name__ == "__main__":
    main()
```

**Uso:**
```bash
python3 dashboardesp.py                  # auto-detect puerto
python3 dashboardesp.py /dev/ttyUSB0     # puerto explicito
```

### 6.2 `reader_srne.py` — Lector serial con log CSV

```bash
python3 reader_srne.py                  # muestra en pantalla
python3 reader_srne.py --log            # guarda a archivo CSV
python3 reader_srne.py --csv            # output CSV en pantalla
```

### 6.3 `test_modbus_srne.py` — Prueba de comunicacion Modbus

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

# 2. Log CSV
python3 reader_srne.py --log

# 3. Debug (ver JSON crudo)
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
