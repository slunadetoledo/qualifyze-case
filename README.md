# Qualifyze Data Engineer Technical Case

Este repositorio contiene la solución al caso técnico para el rol de Data Engineer. [cite_start]El proyecto aborda la ingesta de datos regulatorios de la base de datos pública **EudraGMDP** (gestionada por la EMA) y el diseño de un sistema de monitoreo para informes de no cumplimiento (NCR)[cite: 14, 65].

---

## 1. Arquitectura del Sistema

Se ha implementado una arquitectura de datos basada en el patrón **Pseudo-Medallion** sobre una base de datos **PostgreSQL**. [cite_start]La orquestación de todo el entorno se realiza mediante **Docker**, garantizando la reproducibilidad tanto en Linux como en macOS[cite: 50, 51].

### Capas de Datos:
* [cite_start]**Bronze (Raw)**: Ingestión directa desde el archivo Excel suministrado utilizando **Python**[cite: 17, 52]. [cite_start]Los datos se almacenan sin transformaciones para asegurar la trazabilidad absoluta del origen[cite: 9, 14].
* **Silver (Staging)**: Transformación y limpieza mediante **dbt**. [cite_start]Se normalizan los nombres de las columnas, se aplican tipos de datos correctos y se parsean las fechas críticas como `Inspection End Date` e `Issue Date`[cite: 38, 39, 51].
* [cite_start]**Gold (Analytics/Marts)**: Capa de consumo final donde se aplica la lógica de negocio y se preparan los datos para el usuario final[cite: 42].

---

## 2. Decisiones Clave y Asunciones

* [cite_start]**Mapeo de Identidades**: El enunciado especifica que los identificadores de sitios en la fuente pública difieren de los internos de Qualifyze[cite: 16]. 
    * [cite_start]**Asunción**: Ante la falta de una tabla de mapeo de terceros, se utiliza el `OMS Location Identifier` y el `DUNS Number` como claves maestras para la integración[cite: 28, 34].
* [cite_start]**Stack Tecnológico**: Se ha priorizado el uso de **Python + dbt** para alinearse con el stack tecnológico de Qualifyze[cite: 51, 52].
* **Idempotencia**: El script de carga (`ingestion/load_bronze.py`) está diseñado para ser ejecutado múltiples veces sin duplicar registros, asegurando que la capa Bronze siempre refleje el estado más reciente del archivo fuente.

---

## 3. Instrucciones de Configuración y Ejecución

Para que el proyecto funcione en cualquier entorno (incluyendo macOS), sigue estos pasos:

1.  **Requisitos**: Tener instalados Docker y Docker Compose.
2.  [cite_start]**Preparación**: Coloca el archivo Excel en la carpeta `data/EUDRA_export.xls`[cite: 17].
3.  **Despliegue**: Ejecuta el siguiente comando en la raíz del proyecto:
    ```bash
    docker-compose up --build
    ```
Este comando levantará el contenedor de la base de datos, ejecutará el script de carga de Python y aplicará los modelos de dbt automáticamente.

---

## 4. Troubleshooting (Entorno de Desarrollo)

Durante el desarrollo en Ubuntu 26.04 y bajo conexiones de red específicas (ej. O2/Movistar), se detectaron y resolvieron los siguientes bloqueos:

* **Timeouts en Docker Pull**: Causados por fragmentación de paquetes en redes PPPoE.
    * *Solución*: Ajuste del **MTU a 1450** en la configuración del demonio de Docker.
* **Conectividad de Red**: Se implementó el uso de **Cloudflare WARP** para estabilizar el peering con los registros de imágenes base.

---

## 5. Parte 2: Sistema de Monitoreo de NCR

[cite_start]El objetivo es detectar automáticamente nuevos **Non-Compliance Reports (NCR)**[cite: 63, 65].

### Diseño Propuesto:
1.  [cite_start]**Detección de Deltas**: El pipeline de ingesta compara el `EudraGMDP Document Reference Number` de cada carga[cite: 22].
2.  [cite_start]**Evaluación de Criticidad**: Se filtran específicamente los registros cuyo `Document Type` sea "Non-Compliance Report"[cite: 23, 63].
3.  **Flujo de Notificación**: 
    * Se dispara una alerta inmediata a los stakeholders mediante un bus de eventos (o sensor de Dagster).
    * [cite_start]Se actualiza el registro interno del sitio para reflejar el estado de "No Cumplimiento" de forma inmediata[cite: 65].

---

## 6. Ideas para Mejorar y Escalar

* [cite_start]**Automatización de Mapeo**: Implementar un sistema de *Fuzzy Matching* basado en `Site Name` y dirección postal para reducir la fricción en la vinculación de IDs[cite: 16, 29, 30].
* [cite_start]**Ingesta Directa**: Sustituir el procesamiento de archivos Excel por una integración directa con la **API de EudraGMDP (EMA)** para reducir la latencia de los datos[cite: 10, 11].
* **Validación de Calidad**: Incorporar `dbt-tests` y `Great Expectations` para validar esquemas y reglas de negocio en la capa Silver antes de su consumo en Gold.

---