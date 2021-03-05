import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
import requests
import os

# download 'tagebuch' csv from fddb.info
url = 'https://fddb.info/db/i18n/exporter/?lang=de&action=diary&type=csv'
fddb_user = os.environ['FDDB_USER']
fddb_pw = os.environ['FDDB_PW']
headers = {'cookie': 'fddb=' + os.environ['FDDB_COOKIE']}
resp = requests.get(url, auth=(fddb_user, fddb_pw), headers=headers)

# write downloaded csv to file
with open('filename.csv', 'wb') as fd:
    for chunk in resp.iter_content(chunk_size=128):
        fd.write(chunk)

#open csv as dataframe
df = pd.read_csv('filename.csv', sep=';')
# remove unused columns
df = df.drop(columns=['bezeichnung', 'interne_id', 'kj_aktivitaeten', 'fett_g', 'kh_g', 'protein_g'] )

# convert to date format
df['id'] = pd.to_datetime(df.datum_tag_monat_jahr_stunde_minute, format='%d.%m.%Y %H:%M')

# remove empty trailing column
df = df.dropna(axis='columns')
# remove old date column
df = df.drop(columns=['datum_tag_monat_jahr_stunde_minute'])

# resample to aggregate on daily basis
sums = df.set_index('id').resample('D').sum()

# create a date column with values from index (somehow necessary for sql upsert)
sums['date'] = sums.index

# remove empty rows
sums = sums[sums.kj != 0]

# convert to kcal
sums['kj'] = sums['kj'] *  0.2388
# convert to integer
sums['kj'] = pd.Series(sums['kj']).astype(int)

# create database engine
engine = create_engine(os.environ['FDDB_POSTGRES'])

print("inserting into database")

# insert / upsert into database
with engine.begin() as conn:
    # step 1 - create temporary table and upload DataFrame (necessary for upsert)
    conn.execute(
        text(
            "CREATE TEMPORARY TABLE temp_table (date DATE PRIMARY KEY, kj INT)"
        )
    )
    sums.to_sql("temp_table", conn, index=False, if_exists="append")

    # step 2 - merge temp_table into main_table
    conn.execute(
        text("""\
            INSERT INTO fddb (date, kj) 
            SELECT date, kj FROM temp_table
            ON CONFLICT (date) DO
                UPDATE SET kj = EXCLUDED.kj
            """
        )
    )

