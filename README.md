# Sistema de Monitorización Fotovoltaica — Aulas Sostenibles

Repositorio del proyecto de grado para el diseño e implementación de un sistema de monitorización de los sistemas fotovoltaicos en las aulas sostenibles de la **Universidad del Magdalena**.

## Infraestructura objetivo

- **3 inversores modernos** (HF2430U80-H) — bancos de baterías **Green Point 25.6V 200AH**
- **4 inversores** pendientes de sensado
- **1 inversor** en espera de actualización
- Vías de comunicación: **serial** (posible software propietario) y **Modbus**

## Estructura del repositorio

- `00_DOCUMENTACION_PRINCIPAL/` — Anteproyecto, informe final y presentaciones
- `01_INVESTIGACION_Y_BASE_CONOCIMIENTO/` — Datasheets, notas técnicas, referencias y normas
- `02_DISENO_HARDWARE/` — Esquemáticos, PCB, simulaciones e imágenes
- `03_FIRMWARE/` — Código fuente del ESP32 (PlatformIO/ESP-IDF)
- `04_SOFTWARE_PC/` — Scripts y herramientas auxiliares para PC
- `05_MEDICIONES_Y_ENSAYOS/` — Datos de validación y pruebas de laboratorio
- `06_GESTION_DEL_PROYECTO/` — Planificación, presupuesto y bitácora

## Requisitos mínimos

- KiCad (esquemáticos y PCB)
- PlatformIO + ESP-IDF (firmware)
- Python 3.x + dependencias (software PC)

## Créditos

Proyecto de grado — Universidad del Magdalena — Autor
