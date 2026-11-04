"""Download public ONS sources and retain a small, traceable Liverpool snapshot."""
import argparse
import csv
import hashlib
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
TABLES = ('ts007a', 'ts054', 'ts066')
SERVICE = ('https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/'
           'Middle_layer_Super_Output_Areas_December_2021_Boundaries_EW_BGC_V3/FeatureServer/0')
BOUNDARY_URL = SERVICE + '/query?' + urlencode({
    'where': "MSOA21NM LIKE 'Liverpool %'", 'outFields': 'MSOA21CD,MSOA21NM,BNG_E,BNG_N,LAT,LONG',
    'outSR': '4326', 'f': 'geojson', 'returnGeometry': 'true'})


def sha(data):
    return hashlib.sha256(data).hexdigest()


def download(url):
    with urlopen(url, timeout=90) as response:
        return response.read()


def build_snapshot(out, cache=None):
    out.mkdir(parents=True, exist_ok=True)
    geo_bytes = (cache/'boundaries.geojson').read_bytes() if cache else download(BOUNDARY_URL)
    geo = json.loads(geo_bytes)
    if geo.get('exceededTransferLimit') or not geo.get('features'):
        raise ValueError('Boundary response is empty or truncated')
    codes = {f['properties']['MSOA21CD'] for f in geo['features']}
    if len(codes) != len(geo['features']) or len(codes) != 61:
        raise ValueError('Expected the 61 unique Liverpool MSOAs in the pinned 2021 release')
    for feature in geo['features']:
        if not feature['properties']['MSOA21NM'].startswith('Liverpool '):
            raise ValueError('Unexpected boundary area')
    (out/'boundaries.geojson').write_bytes(geo_bytes)
    manifest = {'retrieved_at': datetime.now(timezone.utc).isoformat(),
                'census_date': '2021-03-21', 'area_type': 'MSOA 2021',
                'area_count': len(codes), 'city_code': 'E08000012', 'country_code': 'E92000001',
                'files': {'boundaries.geojson': {'sha256': sha(geo_bytes), 'url': BOUNDARY_URL,
                    'publisher': 'Office for National Statistics, Open Geography Portal',
                    'release': 'MSOA December 2021 BGC V3 (July 2024 boundary maintenance)'}},
                'note': 'CSV extracts retain original headers and counts for 61 MSOAs plus Liverpool LTLA and England. National archives are not redistributed.'}
    for table in TABLES:
        url = f'https://www.nomisweb.co.uk/output/census/2021/census2021-{table}.zip'
        body = (cache/(table+'.zip')).read_bytes() if cache else download(url)
        selected = []
        members = []
        metadata = {}
        with ZipFile(io.BytesIO(body)) as archive:
            for level, wanted in [('msoa', codes), ('ltla', {'E08000012'}), ('ctry', {'E92000001'})]:
                name = f'census2021-{table}-{level}.csv'
                source = archive.read(name)
                reader = csv.DictReader(io.StringIO(source.decode('utf-8-sig')))
                rows = [r for r in reader if r['geography code'] in wanted]
                if {r['geography code'] for r in rows} != wanted or len(rows) != len(wanted):
                    raise ValueError(f'{name}: area coverage differs from boundaries')
                if selected and list(selected[0]) != reader.fieldnames:
                    raise ValueError('Source column definitions differ between levels')
                selected += rows
                members.append({'member': name, 'sha256': sha(source), 'selected_rows': len(rows)})
            for name in archive.namelist():
                if name.startswith('metadata/'):
                    metadata[name] = archive.read(name).decode('utf-8-sig')
        dest = out/(table+'.csv')
        with dest.open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(selected[0]))
            writer.writeheader(); writer.writerows(selected)
        manifest['files'][dest.name] = {'sha256': sha(dest.read_bytes()), 'url': url,
            'publisher': 'Office for National Statistics via Nomis', 'archive_sha256': sha(body),
            'members': members, 'archive_metadata': metadata,
            'dataset_page': f'https://www.nomisweb.co.uk/datasets/c2021{table}'}
    (out/'provenance.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(f'Saved 61 MSOAs, Liverpool and England for {len(TABLES)} datasets.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--from-cache', type=Path, help='Use already-downloaded official archive bytes')
    parser.add_argument('--output', type=Path, default=ROOT/'data/raw')
    args = parser.parse_args()
    build_snapshot(args.output, args.from_cache)
