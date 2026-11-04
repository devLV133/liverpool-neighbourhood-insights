"""Export the checked source tables to a standalone SQL Server setup script."""
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from analyse import build_database


def quote(value):
    return "N'"+value.replace("'","''")+"'" if isinstance(value,str) else str(value)


def build():
    con,_,_=build_database(ROOT/'data/raw')
    parts=['-- Liverpool Neighbourhood Insights | Census 2021',
           '-- Run in a new empty SQL Server database. Creates tables and views; does not drop existing objects.',
           '-- Generated from the validated snapshot. SQL Server runtime execution is not verified.',
           'SET XACT_ABORT ON;\nGO',
           (ROOT/'sql/schema.sql').read_text().replace('TEXT','NVARCHAR(180)'), 'GO']
    for table in ['areas','age_counts','tenure_counts','employment_counts']:
        records=list(con.execute('SELECT * FROM '+table+' ORDER BY area_code'))
        parts.append('INSERT INTO '+table+' VALUES\n'+',\n'.join('('+', '.join(quote(v) for v in r)+')' for r in records)+';\nGO')
    views=(ROOT/'sql/views.sql').read_text()
    # CREATE VIEW must be the first statement of its batch.
    parts.extend(v.strip()+';\nGO' for v in views.split(';') if v.strip())
    parts.append('SELECT * FROM neighbourhood_comparison ORDER BY area_code;\nGO')
    (ROOT/'sql/sql_server_setup.sql').write_text('\n\n'.join(parts)+'\n')
    con.close()
    print('Built SQL Server setup for 63 areas and three source tables.')


if __name__=='__main__':build()
