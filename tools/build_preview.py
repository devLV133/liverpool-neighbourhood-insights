"""Render static analytical previews from the checked data, not UI screenshots."""
import json
import math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from matplotlib.colors import LinearSegmentedColormap, Normalize

ROOT=Path(__file__).resolve().parents[1]


def build():
    data=json.loads((ROOT/'data/processed/dashboard.json').read_text())
    geo=json.loads((ROOT/'data/raw/boundaries.geojson').read_text())
    rows=data['neighbourhoods']; city=next(r for r in data['benchmarks'] if r['area_type']=='City')
    england=next(r for r in data['benchmarks'] if r['area_type']=='Country')
    metric='social_rented_share';values={r['area_code']:r[metric]*100 for r in rows}
    ink='#15333b';teal='#087e86';muted='#52676d'
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'text.color':ink,'axes.labelcolor':ink,'xtick.color':muted,'ytick.color':muted})
    fig=plt.figure(figsize=(13,8),facecolor='#f3f6f5')
    fig.text(.055,.94,'LIVERPOOL / CENSUS 2021',fontsize=10,color=teal,weight='bold')
    fig.text(.055,.887,'Neighbourhood Insights',fontsize=28,weight='bold')
    fig.text(.055,.847,'61 statistical areas. Three indicators. A consistent historical baseline.',fontsize=12,color=muted)
    for x,(key,definition) in zip([.055,.37,.69],data['definitions'].items()):
        fig.text(x,.785,definition['label'],fontsize=10,weight='bold')
        fig.text(x,.731,f'{city[key]:.1%}',fontsize=25,weight='bold')
        fig.text(x+.10,.738,f'Liverpool  |  England {england[key]:.1%}',fontsize=9,color=muted)
    ax=fig.add_axes([.045,.15,.43,.48]);ax.set_facecolor('#f3f6f5')
    cmap=LinearSegmentedColormap.from_list('local',['#dcece8','#076980']);norm=Normalize(min(values.values()),max(values.values()))
    c=math.cos(math.radians(53.4));patches=[];colours=[]
    for f in geo['features']:
        polygons=[f['geometry']['coordinates']] if f['geometry']['type']=='Polygon' else f['geometry']['coordinates']
        for poly in polygons:
            # Exterior rings suffice for this static choropleth preview.
            patches.append(Polygon([(p[0]*c,p[1]) for p in poly[0]],closed=True))
            colours.append(values[f['properties']['MSOA21CD']])
    collection=PatchCollection(patches,cmap=cmap,norm=norm,edgecolor='white',linewidth=.5)
    collection.set_array(colours);ax.add_collection(collection);ax.autoscale_view();ax.set_aspect('equal');ax.axis('off')
    ax.set_title('Socially rented households',loc='left',pad=10,fontsize=13,weight='bold')
    cbax=fig.add_axes([.10,.115,.32,.013]);cb=fig.colorbar(collection,cax=cbax,orientation='horizontal');cb.ax.tick_params(labelsize=8,length=0);cb.outline.set_visible(False)
    fig.text(.10,.085,'Share of households (%) · 2021 MSOA boundaries',fontsize=8,color=muted)
    chart=fig.add_axes([.60,.18,.33,.44]);ranked=sorted(rows,key=lambda r:r[metric],reverse=True)[:10]
    chart.barh([r['area_name'] for r in ranked],[100*r[metric] for r in ranked],color=teal,height=.57)
    chart.invert_yaxis();chart.set_xlim(0,65);chart.set_xlabel('Share of households (%)',fontsize=9)
    chart.axvline(100*city[metric],color=ink,ls='--',lw=1)
    chart.text(100*city[metric]+1,9.9,f'Liverpool {city[metric]:.1%}',fontsize=8,color=ink)
    for i,r in enumerate(ranked):chart.text(100*r[metric]+.7,i,f'{r[metric]:.1%}',va='center',fontsize=9)
    chart.set_title('Ten highest social-renting shares',loc='left',pad=18,fontsize=13,weight='bold')
    chart.set_facecolor('#f3f6f5');chart.tick_params(axis='both',length=0)
    for spine in chart.spines.values():spine.set_visible(False)
    fig.text(.055,.05,'ONS Census 2021 via Nomis • TS007A / TS054 / TS066 • Independent portfolio analysis',fontsize=8,color=muted)
    fig.text(.055,.03,'Contains OS and National Statistics data © Crown copyright and database right 2026. Open Government Licence v3.0.',fontsize=8,color=muted)
    fig.text(.055,.01,'Static analytical preview. The interactive report includes area selection, comparisons and CSV export.',fontsize=8,color=muted)
    out=ROOT/'docs/images';out.mkdir(exist_ok=True)
    fig.savefig(out/'analysis-preview.png',dpi=160,facecolor=fig.get_facecolor());plt.close(fig)
    print('Rendered static analytical preview.')


if __name__=='__main__':build()
