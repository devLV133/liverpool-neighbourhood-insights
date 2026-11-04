"""Validate PBIR JSON against Microsoft's schemas and check model references.

Requires jsonschema (development only) and internet on first use. Schemas are
cached outside the repository. This is not a Power BI Desktop execution test.
"""
import json
import sys
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from jsonschema import Draft7Validator
from referencing import Registry, Resource

ROOT=Path(__file__).resolve().parents[1]
CACHE=Path(tempfile.gettempdir())/'council-insights-schemas'


def fetch(uri):
    uri=uri.split('#')[0]
    parsed=urlparse(uri)
    if parsed.hostname!='developer.microsoft.com' or not parsed.path.startswith('/json-schemas/'):
        raise ValueError('Unexpected schema host: '+uri)
    relative=parsed.path.removeprefix('/json-schemas/').replace('schema.embedded.json','schema-embedded.json')
    if '..' in Path(relative).parts: raise ValueError('Unexpected schema path')
    local=CACHE/relative
    if not local.exists():
        request='https://raw.githubusercontent.com/microsoft/json-schemas/main/'+relative
        body=urllib.request.urlopen(request,timeout=30).read()
        json.loads(body)
        local.parent.mkdir(parents=True,exist_ok=True);local.write_bytes(body)
    return json.loads(local.read_text())


def main():
    model=json.loads((ROOT/'powerbi/LiverpoolInsights.SemanticModel/model.bim').read_text())['model']
    tables={t['name']:t for t in model['tables']}
    columns={name:{c['name'] for c in t['columns']} for name,t in tables.items()}
    measures={name:{c['name'] for c in t.get('measures',[])} for name,t in tables.items()}
    for rel in model['relationships']:
        assert rel['fromColumn'] in columns[rel['fromTable']]
        assert rel['toColumn'] in columns[rel['toTable']]
    registry=Registry(retrieve=lambda uri: Resource.from_contents(fetch(uri)))
    count=0
    for path in sorted((ROOT/'powerbi').rglob('*')):
        if path.suffix not in {'.json','.pbip','.pbir','.pbism'}: continue
        data=json.loads(path.read_text());uri=data['$schema'];schema=fetch(uri)
        errors=list(Draft7Validator(schema,registry=registry).iter_errors(data))
        if errors:raise ValueError(f'{path.relative_to(ROOT)}: {errors[0].message}')
        for state in data.get('visual',{}).get('query',{}).get('queryState',{}).values():
            for p in state['projections']:
                typ,expr=next(iter(p['field'].items()))
                table=expr['Expression']['SourceRef']['Entity']
                assert expr['Property'] in (measures if typ=='Measure' else columns)[table],p
        count+=1
    print(f'{count} Power BI JSON files pass Microsoft schema validation. All visual field references resolve.')
    print('Power BI Desktop refresh, DAX execution and visual rendering have not been verified.')


if __name__=='__main__':main()
