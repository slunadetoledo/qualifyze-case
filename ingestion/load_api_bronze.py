import os
import pandas as pd
from sqlalchemy import create_engine, text
import requests
from datetime import datetime
import re

# 1. Configuración de conexión
DB_URL = os.getenv("DB_URL", "postgresql://qualifyze_user:qualifyze_password@db:5432/qualifyze_dw")
engine = create_engine(DB_URL)

def fetch_from_api(api_url):
    """Descarga datos paginados desde la API y devuelve un DataFrame."""
    all_data = []
    page = 1
    while True:
        print(f"📡 Obteniendo página {page}...")
        # Ajusta los parámetros de paginación o headers según la API
        response = requests.get(api_url, params={"page": page, "limit": 100})
        response.raise_for_status()
        
        data = response.json()
        records = data.get("results", [])
        if not records:
            break
            
        all_data.extend(records)
        page += 1
        
    return pd.DataFrame(all_data)

def run_api_ingestion():
    api_url = os.getenv("EUDRA_API_URL", "https://api.ema.europa.eu/eudragmdp/v1/ncr")
    print(f"🚀 Iniciando ingesta desde API: {api_url}")

    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS bronze;"))
        conn.commit()

    dtypes = {
        'OMS Organisation Identifier': str,
        'OMS Location Identifier': str,
        'DUNS Number': str,
        'Postcode': str,
        'Certificate Number': str
    }

    try:
        df = fetch_from_api(api_url)
        if not df.empty:
            for col, col_type in dtypes.items():
                if col in df.columns:
                    df[col] = df[col].astype(col_type)
            
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
            
            expected_cols = [
                'document_reference_number', 'certificate_number', 'oms_organisation_id',
                'oms_location_id', 'duns_number', 'site_name', 'postcode',
                'document_type', 'inspection_end_date', 'issue_date'
            ]
            for c in expected_cols:
                if c not in df.columns:
                    df[c] = None

            df['_ingested_at'] = datetime.now()
            batch_id = datetime.now().strftime("%Y%m%d%H%M%S")
            df['_source_file'] = f"api_batch_{batch_id}"

            df.to_sql('raw_eudragmdp', con=engine, schema='bronze', if_exists='append', index=False, chunksize=1000)
            print(f"✅ {len(df)} registros procesados en el lote API {batch_id}")

    except Exception as e:
        print(f"💥 Error en la ingesta por API: {str(e)}")

if __name__ == "__main__":
    run_api_ingestion()