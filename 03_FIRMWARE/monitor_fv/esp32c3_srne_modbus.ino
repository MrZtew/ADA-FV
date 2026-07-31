/*
  ============================================================================
  MONITOR FV — SRNE HF2430U80-H
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
    PC (dashboardesp.py / serverweb_srne.py / reader_srne.py)

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
  Serial.println("{\"t\":\"init\",\"msg\":\"Monitor FV encendido\"}");
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
