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

# English Version

## Qualifyze Data Engineer Technical Case

This repository contains the solution to the technical case for the Data Engineer role. The project addresses the ingestion of regulatory data from the public **EudraGMDP** database (managed by the EMA) and the design of a monitoring system for non-compliance reports (NCR).

---

## 1. System Architecture

A data architecture based on the **Pseudo-Medallion** pattern has been implemented on a **PostgreSQL** database. The orchestration of the entire environment is done using **Docker**, ensuring reproducibility on both Linux and macOS.

### Data Layers:
* **Bronze (Raw)**: Direct ingestion from the provided Excel file using **Python**. The data is stored without transformations to ensure absolute traceability of the origin.
* **Silver (Staging)**: Transformation and cleaning using **dbt**. Column names are normalized, correct data types are applied, and critical dates like `Inspection End Date` and `Issue Date` are parsed.
* **Gold (Analytics/Marts)**: Final consumption layer where business logic is applied and data is prepared for the end user.

---

## 2. Key Decisions and Assumptions

* **Identity Mapping**: The problem statement specifies that site identifiers in the public source differ from Qualifyze's internal ones. 
    * **Assumption**: In the absence of a third-party mapping table, the `OMS Location Identifier` and `DUNS Number` are used as master keys for integration.
* **Tech Stack**: The use of **Python + dbt** has been prioritized to align with Qualifyze's technology stack.
* **Idempotency**: The load script (`ingestion/load_bronze.py`) is designed to be executed multiple times without duplicating records, ensuring that the Bronze layer always reflects the most recent state of the source file.

---

## 3. Setup and Execution Instructions

For the project to work in any environment (including macOS), follow these steps:

1.  **Requirements**: Have Docker and Docker Compose installed.
2.  **Preparation**: Place the Excel file in the `data/EUDRA_export.xls` folder.
3.  **Deployment**: Run the following command in the root of the project:
    ```bash
    docker-compose up --build
    ```
This command will spin up the database container, execute the Python load script, and apply the dbt models automatically.

---

## 4. Troubleshooting (Development Environment)

During development on Ubuntu 26.04 and under specific network connections (e.g., O2/Movistar), the following blocks were detected and resolved:

* **Timeouts in Docker Pull**: Caused by packet fragmentation in PPPoE networks.
    * *Solution*: Adjusted the **MTU to 1450** in the Docker daemon configuration.
* **Network Connectivity**: Implemented the use of **Cloudflare WARP** to stabilize peering with base image registries.

---

## 5. Part 2: NCR Monitoring System

The goal is to automatically detect new **Non-Compliance Reports (NCR)**.

### Proposed Design:
1.  **Delta Detection**: The ingestion pipeline compares the `EudraGMDP Document Reference Number` of each load.
2.  **Criticality Assessment**: Records whose `Document Type` is "Non-Compliance Report" are specifically filtered.
3.  **Notification Flow**: 
    * An immediate alert is triggered to stakeholders via an event bus (or Dagster sensor).
    * The internal site record is updated to reflect the "Non-Compliant" status immediately.

---

## 6. Ideas for Improvement and Scaling

* **Mapping Automation**: Implement a *Fuzzy Matching* system based on `Site Name` and postal address to reduce friction in ID linking.
* **Direct Ingestion**: Replace Excel file processing with direct integration with the **EudraGMDP (EMA) API** to reduce data latency.
* **Quality Validation**: Incorporate `dbt-tests` and `Great Expectations` to validate schemas and business rules in the Silver layer before consumption in Gold.

---