"""Validate the pinned public-data snapshot, run SQL and export dashboard inputs.

The default build is offline and uses only the Python standard library.
"""
import argparse
import csv
import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CITY, ENGLAND = 'E08000012', 'E92000001'
AGE_TOTAL = 'Age: Total'
AGE_65 = [f'Age: Aged {s} years' for s in ('65 to 69', '70 to 74', '75 to 79', '80 to 84')]
AGE_65 += ['Age: Aged 85 years and over']
HH_TOTAL = 'Tenure of household: Total: All households'
SOCIAL = 'Tenure of household: Social rented'
ECON_TOTAL = 'Economic activity status: Total: All usual residents aged 16 years and over'
EMP_NON = 'Economic activity status: Economically active (excluding full-time students):In employment'
EMP_STUDENT = 'Economic activity status: Economically active and a full-time student:In employment'
DEFINITIONS = {
    'aged_65_share': {'label': 'Residents aged 65+', 'denominator': 'All usual residents', 'numerator': 'aged_65_plus', 'base': 'population', 'source': 'TS007A'},
    'social_rented_share': {'label': 'Socially rented households', 'denominator': 'All households', 'numerator': 'social_rented', 'base': 'households', 'source': 'TS054'},
    'employed_share': {'label': 'Residents aged 16+ in employment', 'denominator': 'All usual residents aged 16+', 'numerator': 'employed', 'base': 'residents_16_plus', 'source': 'TS066'},
}


def read_table(path, required):
    with path.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        if not set(required + ['date', 'geography', 'geography code']) <= set(reader.fieldnames or []):
            raise ValueError(f'{path.name}: missing required columns')
        result = {}
        for row in reader:
            code = row['geography code']
            if code in result:
                raise ValueError(f'{path.name}: duplicate geography {code}')
            if row['date'] != '2021' or not row['geography'].strip():
                raise ValueError(f'{path.name}: wrong period or missing area name')
            for col in required:
                value = row[col]
                if not value.isascii() or not value.isdigit():
                    raise ValueError(f'{path.name}: invalid or missing count for {code}: {col}')
                row[col] = int(value)
            result[code] = row
    return result


def build_database(raw, check_hashes=True):
    provenance = json.loads((raw/'provenance.json').read_text())
    if check_hashes:
        for name, meta in provenance['files'].items():
            if Path(name).name != name:
                raise ValueError('Invalid manifest filename')
            actual = hashlib.sha256((raw/name).read_bytes()).hexdigest()
            if actual != meta['sha256']:
                raise ValueError(f'{name}: snapshot checksum mismatch')
    geo = json.loads((raw/'boundaries.geojson').read_text())
    features = geo['features']
    codes = {f['properties']['MSOA21CD'] for f in features}
    if len(codes) != len(features) or len(codes) != 61:
        raise ValueError('Expected 61 unique MSOA boundaries')
    if any(f['geometry']['type'] not in ('Polygon', 'MultiPolygon') for f in features):
        raise ValueError('Expected polygon boundaries')
    names = {f['properties']['MSOA21CD']: f['properties']['MSOA21NM'] for f in features}
    age = read_table(raw/'ts007a.csv', [AGE_TOTAL]+AGE_65)
    tenure = read_table(raw/'ts054.csv', [HH_TOTAL, SOCIAL])
    econ = read_table(raw/'ts066.csv', [ECON_TOTAL, EMP_NON, EMP_STUDENT])
    expected = codes | {CITY, ENGLAND}
    if any(set(t) != expected for t in (age, tenure, econ)):
        raise ValueError('Source and boundary geography coverage does not match')
    con = sqlite3.connect(':memory:')
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    con.executescript((ROOT/'sql/schema.sql').read_text())
    for code in sorted(expected):
        a, h, e = age[code], tenure[code], econ[code]
        if len({a['geography'], h['geography'], e['geography'], names.get(code, a['geography'])}) != 1:
            raise ValueError('Conflicting names for '+code)
        kind = 'City' if code == CITY else 'Country' if code == ENGLAND else 'MSOA'
        con.execute('INSERT INTO areas VALUES (?,?,?)', (code, a['geography'], kind))
        con.execute('INSERT INTO age_counts VALUES (?,?,?)', (code, a[AGE_TOTAL], sum(a[c] for c in AGE_65)))
        con.execute('INSERT INTO tenure_counts VALUES (?,?,?)', (code, h[HH_TOTAL], h[SOCIAL]))
        con.execute('INSERT INTO employment_counts VALUES (?,?,?,?)', (code, e[ECON_TOTAL], e[EMP_NON], e[EMP_STUDENT]))
    con.executescript((ROOT/'sql/views.sql').read_text())
    return con, geo, provenance


def query(con, sql):
    return [dict(r) for r in con.execute(sql)]


def write_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def run(raw=ROOT/'data/raw', output=ROOT/'data/processed'):
    con, geo, provenance = build_database(raw)
    output.mkdir(parents=True, exist_ok=True)
    areas = query(con, 'SELECT * FROM neighbourhood_comparison ORDER BY area_code')
    benchmarks = query(con, "SELECT * FROM area_indicators WHERE area_type <> 'MSOA' ORDER BY area_code")
    city = next(r for r in benchmarks if r['area_code'] == CITY)
    pooled = query(con, 'SELECT * FROM pooled_msoa_control')[0]
    control = [{'measure': k, 'sum_msoa': pooled[k], 'published_city': city[k], 'difference': pooled[k]-city[k]}
               for k in ('population','aged_65_plus','households','social_rented','residents_16_plus','employed')]
    points = {f['properties']['MSOA21CD']: f['properties'] for f in geo['features']}
    for row in areas:
        row['latitude'] = points[row['area_code']]['LAT']
        row['longitude'] = points[row['area_code']]['LONG']
    write_csv(output/'neighbourhoods.csv', areas)
    write_csv(output/'benchmarks.csv', benchmarks)
    write_csv(output/'reconciliation.csv', control)
    write_csv(output/'context.csv', [{'census_date':'2021-03-21', 'source_retrieved':provenance['retrieved_at'][:10], 'areas':len(areas)}])
    payload = {'census_date':'2021-03-21', 'retrieved_at':provenance['retrieved_at'],
               'definitions':DEFINITIONS, 'neighbourhoods':areas, 'benchmarks':benchmarks,
               'reconciliation':control}
    (output/'dashboard.json').write_text(json.dumps(payload, indent=2)+'\n')
    (output/'quality.json').write_text(json.dumps({'status':'passed','matched_areas':len(areas),
        'checks':['Snapshot SHA-256','Unique area keys','2021 dates','Exact source / boundary coverage',
                  'Consistent area names','Non-negative integer counts','Positive denominators','Numerators within denominators'],
        'reconciliation_note':'Published city counts and sums of small areas can differ because of Census disclosure control. Differences are retained, not silently adjusted.'}, indent=2)+'\n')
    db = output/'insights.sqlite'
    if db.exists(): db.unlink()
    with sqlite3.connect(db) as target: con.backup(target)
    con.close()
    print(f'Validated and analysed {len(areas)} Liverpool MSOAs; 3 indicators and 2 published benchmarks.')
    return payload


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw', type=Path, default=ROOT/'data/raw')
    parser.add_argument('--output', type=Path, default=ROOT/'data/processed')
    args = parser.parse_args()
    run(args.raw, args.output)
