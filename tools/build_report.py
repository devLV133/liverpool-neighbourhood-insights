"""Build a portable two-page analytical report with an embedded offline SVG map."""
import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rings(geometry):
    return geometry['coordinates'] if geometry['type'] == 'Polygon' else [r for poly in geometry['coordinates'] for r in poly]


def map_paths(geo):
    # Local equirectangular display at Liverpool's latitude, north upwards.
    # Analysis joins use area codes, never displayed coordinates or map areas.
    c = math.cos(math.radians(53.4))
    project = lambda p: (p[0]*c, -p[1])
    points = [project(p) for f in geo['features'] for r in rings(f['geometry']) for p in r]
    xmin,ymin = map(min, zip(*points)); xmax,ymax = map(max, zip(*points))
    scale = min(470/(xmax-xmin), 350/(ymax-ymin))
    ox,oy = (520-(xmax-xmin)*scale)/2, (390-(ymax-ymin)*scale)/2
    paths = []
    for f in geo['features']:
        parts=[]
        for ring in rings(f['geometry']):
            pts=[project(p) for p in ring]
            parts.append('M'+' L'.join(f'{ox+(x-xmin)*scale:.2f},{oy+(y-ymin)*scale:.2f}' for x,y in pts)+' Z')
        code=html.escape(f['properties']['MSOA21CD'], quote=True)
        name=html.escape(f['properties']['MSOA21NM'])
        paths.append(f'<path data-code="{code}" d="{" ".join(parts)}" fill-rule="evenodd" tabindex="0" role="button"><title>{name}</title></path>')
    return '\n'.join(paths)


def findings(data):
    city=next(r for r in data['benchmarks'] if r['area_type']=='City')
    eng=next(r for r in data['benchmarks'] if r['area_type']=='Country')
    text=['# Liverpool Neighbourhood Insights: findings', '',
          '**Census 2021 baseline | 61 MSOAs | Independent portfolio analysis**', '',
          '## Question', '', 'How did population age, housing tenure and employment vary within Liverpool, and how did Liverpool compare with England?', '',
          '## Published city benchmarks', '',
          '| Indicator | Liverpool | England | Gap (percentage points) |',
          '|---|---:|---:|---:|']
    for key,d in data['definitions'].items():
        text.append(f"| {d['label']} | {city[key]:.1%} | {eng[key]:.1%} | {(city[key]-eng[key])*100:+.1f} |")
    text+=['','## Within-city differences','']
    for key,d in data['definitions'].items():
        ordered=sorted(data['neighbourhoods'],key=lambda r:r[key])
        low,high=ordered[0],ordered[-1]
        text.append(f"- **{d['label']}:** {low['area_name']} ({low['area_code']}) had the lowest share, {low[key]:.1%}; {high['area_name']} ({high['area_code']}) the highest, {high[key]:.1%}.")
    text+=['','## Implications and next questions','',
           'The city average hides substantial differences. Use the map to select areas for closer investigation, then check contemporary evidence before making service decisions. Age share can prompt questions about service accessibility; tenure can inform engagement with housing providers. Neither is a direct measure of need.', '',
           'The employment comparison includes everyone aged 16+, including retirees and full-time students. Investigate age structure and student populations before interpreting a low share as weak employment opportunities. Do not compare this figure directly with a standard 16–64 employment rate.', '',
           'A practical next step would be to discuss one service question with a service manager, add recent service-use data and agree a measurable decision. This project contains no claimed stakeholder interviews, causal effects, cost savings or current demand forecast.', '',
           '## Limits and quality','',
           'All three indicators use the same 2021 MSOA geography and reference period. MSOAs are statistical areas, not today’s electoral wards or Liverpool’s 13 council neighbourhoods. Census 2021 took place during the pandemic. Rates use their own source denominators; employment includes both employed students and employed nonstudents, without adding parent and child categories.', '',
           f"The MSOA population sum is {sum(r['population'] for r in data['neighbourhoods']):,}; the published Liverpool count in TS007A is {city['population']:,}. The difference is retained in [reconciliation.csv](../data/processed/reconciliation.csv), consistent with the small non-additive totals described in ONS disclosure-control guidance. Published city figures supply the dashboard benchmarks.", '',
           'Sources and exact definitions: [methodology](methodology.md), [source register](sources.md). Findings are generated directly from the checked SQL outputs.']
    return '\n'.join(text)+'\n'


def build():
    data=json.loads((ROOT/'data/processed/dashboard.json').read_text())
    geo=json.loads((ROOT/'data/raw/boundaries.geojson').read_text())
    template=(ROOT/'tools/report_template.html').read_text()
    output=template.replace('__PATHS__',map_paths(geo)).replace('__DATE__',data['retrieved_at'][:10])
    output=output.replace('__DATA__',json.dumps(data).replace('<','\\u003c'))
    (ROOT/'reports').mkdir(exist_ok=True)
    (ROOT/'reports/dashboard.html').write_text(output,encoding='utf-8')
    (ROOT/'docs/findings.md').write_text(findings(data),encoding='utf-8')
    print('Built offline report: 2 pages, 61 selectable polygons, 3 indicators; findings refreshed.')


if __name__ == '__main__': build()
