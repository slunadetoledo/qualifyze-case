# Qualifyze Data Engineer Technical Case

Este repositorio contiene la solución al caso técnico para el rol de Data Engineer. El proyecto aborda la ingesta de datos regulatorios de la base de datos pública **EudraGMDP** (gestionada por la EMA) y el diseño de un sistema de monitoreo para informes de no cumplimiento (NCR).

*This repository contains the solution to the technical case for the Data Engineer role. The project addresses the ingestion of regulatory data from the public **EudraGMDP** database (managed by the EMA) and the design of a monitoring system for Non-Compliance Reports (NCR).*

---

## 1. Arquitectura del Sistema / System Architecture

Se ha implementado una arquitectura de datos basada en el patrón **Pseudo-Medallion** sobre una base de datos **PostgreSQL**. La orquestación de todo el entorno se realiza mediante **Docker**, garantizando la reproducibilidad tanto en Linux como en macOS.

*A data architecture based on the **Pseudo-Medallion** pattern has been implemented on a **PostgreSQL** database. The orchestration of the entire environment is done using **Docker**, ensuring reproducibility on both Linux and macOS.*

### Capas de Datos / Data Layers:
* **Bronze (Raw)**: Ingestión directa desde el archivo Excel suministrado utilizando **Python**. Los datos se almacenan sin transformaciones para asegurar la trazabilidad absoluta del origen. 
  *(Direct ingestion from the provided Excel file using **Python**. Data is stored without transformations to ensure absolute origin traceability.)*
* **Silver (Staging)**: Transformación y limpieza mediante **dbt**. Se normalizan los nombres de las columnas, se aplican tipos de datos correctos y se parsean las fechas críticas como `Inspection End Date` e `Issue Date`. 
  *(Transformation and cleaning using **dbt**. Column names are normalized, correct data types are applied, and critical dates like `Inspection End Date` and `Issue Date` are parsed.)*
* **Gold (Analytics/Marts)**: Capa de consumo final donde se aplica la lógica de negocio y se preparan los datos para el usuario final. 
  *(Final consumption layer where business logic is applied, and data is prepared for the end user.)*

---

## 2. Decisiones Clave y Asunciones / Key Decisions and Assumptions

* **Mapeo de Identidades**: El enunciado especifica que los identificadores de sitios en la fuente pública difieren de los internos de Qualifyze.
    * **Asunción**: Ante la falta de una tabla de mapeo de terceros, se utiliza el `OMS Location Identifier` y el `DUNS Number` como claves maestras para la integración.
  *(**Identity Mapping**: The assignment specifies that site identifiers in the public source differ from Qualifyze's internal ones.)*
    * *(**Assumption**: In the absence of a third-party mapping table, the `OMS Location Identifier` and the `DUNS Number` are used as master keys for integration.)*
* **Stack Tecnológico**: Se ha priorizado el uso de **Python + dbt** para alinearse con el stack tecnológico de Qualifyze.
  *(**Tech Stack**: The use of **Python + dbt** has been prioritized to align with Qualifyze's technology stack.)*
* **Idempotencia**: El script de carga (`ingestion/load_bronze.py`) está diseñado para ser ejecutado múltiples veces sin duplicar registros, asegurando que la capa Bronze siempre refleje el estado más reciente del archivo fuente.
  *(**Idempotency**: The load script (`ingestion/load_bronze.py`) is designed to be executed multiple times without duplicating records, ensuring that the Bronze layer always reflects the most recent state of the source file.)*
* **Método de Ingesta / Ingestion Method**: Actualmente, solo se utiliza el script `load_bronze.py` para la ingesta de datos mediante archivos locales. La ingesta a través de API sería una futura mejora. *(Currently, only the `load_bronze.py` script is used for data ingestion via local files. Data ingestion via API would be a future improvement.)*

---

## 3. Instrucciones de Configuración y Ejecución / Setup and Execution Instructions

Para que el proyecto funcione en cualquier entorno (incluyendo macOS), sigue estos pasos:
*(To make the project work in any environment, including macOS, follow these steps:)*

1.  **Requisitos**: Tener instalados Docker y Docker Compose. 
    *(**Requirements**: Have Docker and Docker Compose installed.)*
2.  **Preparación**: Coloca todos los archivos Excel (`.xls`, `.xlsx`) en la carpeta `data/`. Al menos debe haber 1 archivo. 
    *(**Preparation**: Place all Excel files (`.xls`, `.xlsx`) in the `data/` folder. There must be at least 1 file.)*
3.  **Despliegue**: Ejecuta el siguiente comando en la raíz del proyecto: 
    *(**Deployment**: Run the following command in the project root:)*
    ```bash
    docker-compose up --build
    ```
Este comando levantará el contenedor de la base de datos, ejecutará el script de carga de Python y aplicará los modelos de dbt automáticamente.
*(This command will spin up the database container, execute the Python load script, and apply the dbt models automatically.)*

---

## 4. Troubleshooting (Entorno de Desarrollo) / Troubleshooting (Development Environment)

Durante el desarrollo en Ubuntu 26.04 y bajo conexiones de red específicas (ej. O2/Movistar), se detectaron y resolvieron los siguientes bloqueos:
*(During development on Ubuntu 26.04 and under specific network connections (e.g., O2/Movistar), the following blockers were detected and resolved:)*

* **Timeouts en Docker Pull**: Causados por fragmentación de paquetes en redes PPPoE.
    * *Solución*: Ajuste del **MTU a 1450** en la configuración del demonio de Docker.
  *(**Docker Pull Timeouts**: Caused by packet fragmentation on PPPoE networks.)*
    * *(**Solution**: Adjusted the **MTU to 1450** in the Docker daemon configuration.)*
* **Conectividad de Red**: Se implementó el uso de **Cloudflare WARP** para estabilizar el peering con los registros de imágenes base.
  *(**Network Connectivity**: The use of **Cloudflare WARP** was implemented to stabilize peering with base image registries.)*

---

## 5. Parte 2: Sistema de Monitoreo de NCR / Part 2: NCR Monitoring System

El objetivo es detectar automáticamente nuevos **Non-Compliance Reports (NCR)**.
*(The goal is to automatically detect new **Non-Compliance Reports (NCR)**.)*

### Diseño Propuesto / Proposed Design:
1.  **Detección de Deltas**: El pipeline de ingesta compara el `EudraGMDP Document Reference Number` de cada carga. 
    *(**Delta Detection**: The ingestion pipeline compares the `EudraGMDP Document Reference Number` of each load.)*
2.  **Evaluación de Criticidad**: Se filtran específicamente los registros cuyo `Document Type` sea "Non-Compliance Report". 
    *(**Criticality Evaluation**: Records whose `Document Type` is "Non-Compliance Report" are specifically filtered.)*
3.  **Flujo de Notificación / Notification Flow**: 
    * Se dispara una alerta inmediata a los stakeholders mediante un bus de eventos (o sensor de Dagster). 
      *(An immediate alert is triggered to stakeholders via an event bus or Dagster sensor.)*
    * Se actualiza el registro interno del sitio para reflejar el estado de "No Cumplimiento" de forma inmediata. 
      *(The internal site record is updated to reflect the "Non-Compliance" status immediately.)*

---

## 6. Ideas para Mejorar y Escalar / Ideas for Improvement and Scaling

* **Automatización de Mapeo**: Implementar un sistema de *Fuzzy Matching* basado en `Site Name` y dirección postal para reducir la fricción en la vinculación de IDs.
  *(**Mapping Automation**: Implement a *Fuzzy Matching* system based on `Site Name` and postal address to reduce friction in ID linking.)*
* **Ingesta Directa**: Sustituir el procesamiento de archivos Excel por una integración directa con la **API de EudraGMDP (EMA)** para reducir la latencia de los datos.
  *(**Direct Ingestion**: Replace Excel file processing with direct integration with the **EudraGMDP API (EMA)** to reduce data latency.)*
* **Validación de Calidad**: Incorporar `dbt-tests` y `Great Expectations` para validar esquemas y reglas de negocio en la capa Silver antes de su consumo en Gold.
  *(**Quality Validation**: Incorporate `dbt-tests` and `Great Expectations` to validate schemas and business rules in the Silver layer before consumption in Gold.)*

---
