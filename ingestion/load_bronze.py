import os
import sys
import glob
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import re

# 1. Configuración de conexión
# Usamos 'db' como host porque así se llama el servicio en docker-compose
DB_URL = os.getenv("DB_URL", "postgresql://qualifyze_user:qualifyze_password@db:5432/qualifyze_dw")
engine = create_engine(DB_URL)


def run_ingestion():
    data_dir = "data"
    # Buscamos múltiples archivos excel (.xls, .xlsx) o HTML
    file_paths = glob.glob(os.path.join(data_dir, "*.xls*")) + glob.glob(os.path.join(data_dir, "*.html"))
    
    if not file_paths:
        print(f"❌ Error: No se encontraron archivos en el directorio {data_dir}")
        sys.exit(1)

    print(f"🚀 Iniciando ingesta de {len(file_paths)} archivos...")

    # 2. Creación del esquema Bronze inicial (se hace una sola vez)
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS bronze;"))
        conn.commit()
        print("✅ Esquema 'bronze' verificado.")

    dtypes = {
        'OMS Organisation Identifier': str,
        'OMS Location Identifier': str,
        'DUNS Number': str,
        'Postcode': str,
        'Certificate Number': str
    }

    for file_path in file_paths:
        try:
            print(f"📄 Procesando: {file_path}")
            try:
                # Intentamos leer como Excel binario
                preview_df = pd.read_excel(file_path, header=None, nrows=50, engine='xlrd')
                is_header = preview_df[0].astype(str).str.strip() == 'Certificate Number'
                header_matches = preview_df.index[is_header].tolist()
                if not header_matches:
                    raise ValueError("No se encontró la cabecera 'Certificate Number'.")
                skip_rows = header_matches[0]
                df = pd.read_excel(file_path, dtype=dtypes, skiprows=skip_rows, engine='xlrd')
            except Exception as e:
                # Fallback a HTML
                dfs = pd.read_html(file_path)
                if not dfs:
                    raise ValueError("No se encontraron tablas HTML en el archivo.")
                df = dfs[0]
                if 'Certificate Number' not in df.columns:
                    mask = df.astype(str).apply(lambda x: x.str.strip() == 'Certificate Number')
                    if mask.any().any():
                        row_idx = mask.any(axis=1).idxmax()
                        df.columns = df.iloc[row_idx]
                        df = df.iloc[row_idx + 1:].reset_index(drop=True)
                    else:
                        raise ValueError("No se encontró la cabecera 'Certificate Number'.")
                for col, col_type in dtypes.items():
                    if col in df.columns:
                        df[col] = df[col].astype(col_type)
            
            # 2.5 Normalización de nombres de columnas para Postgres/dbt
            def clean_column(col_name):
                name = str(col_name).replace('\n', ' ').replace('\r', ' ').strip()
                return re.sub(r'[^a-zA-Z0-9]+', '_', name).lower().strip('_')

            df.columns = [clean_column(c) for c in df.columns]

            rename_mapping = {}
            for col in df.columns:
                if 'document_reference_number' in col: rename_mapping[col] = 'document_reference_number'
                elif 'certificate_number' in col: rename_mapping[col] = 'certificate_number'
                elif 'oms_organisation' in col: rename_mapping[col] = 'oms_organisation_id'
                elif 'oms_location' in col: rename_mapping[col] = 'oms_location_id'
                elif 'duns_number' in col: rename_mapping[col] = 'duns_number'
                elif 'site_name' in col: rename_mapping[col] = 'site_name'
                elif 'postcode' in col: rename_mapping[col] = 'postcode'
                elif 'document_type' in col: rename_mapping[col] = 'document_type'
                elif 'inspection_end_date' in col: rename_mapping[col] = 'inspection_end_date'
                elif 'issue_date' in col: rename_mapping[col] = 'issue_date'

            df.rename(columns=rename_mapping, inplace=True)
        
            # Añadir columnas faltantes como NULL para evitar fallos en dbt
            expected_cols = [
                'document_reference_number', 'certificate_number', 'oms_organisation_id',
                'oms_location_id', 'duns_number', 'site_name', 'postcode',
                'document_type', 'inspection_end_date', 'issue_date'
            ]
            for c in expected_cols:
                if c not in df.columns:
                    df[c] = None

            # 3. Metadatos
            df['_ingested_at'] = datetime.now()
            source_file = os.path.basename(file_path)
            df['_source_file'] = source_file

            # 4. Operación Upsert de archivo (Idempotencia)
            with engine.connect() as conn:
                # Verificamos si la tabla existe antes de intentar hacer el DELETE
                table_exists = conn.execute(
                    text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'bronze' AND table_name = 'raw_eudragmdp');")
                ).scalar()
                if table_exists:
                    try:
                        conn.execute(text("DELETE FROM bronze.raw_eudragmdp WHERE _source_file = :f"), {"f": source_file})
                        conn.commit()
                    except Exception:
                        conn.rollback() 

            # Añadimos los datos de este archivo a la tabla Bronze
            df.to_sql('raw_eudragmdp', con=engine, schema='bronze', if_exists='append', index=False, chunksize=1000)
            print(f"✅ {len(df)} registros procesados para {source_file}")

        except Exception as e:
            print(f"💥 Error al procesar {file_path}: {str(e)}")

if __name__ == "__main__":
    run_ingestion()