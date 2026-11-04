"""Generate a native two-page PBIP report and TMSL model from the SQL exports."""
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'powerbi'
BASE='https://developer.microsoft.com/json-schemas/'
NAME='LiverpoolInsights'
TABLES={'Neighbourhoods':'neighbourhoods','Benchmarks':'benchmarks','Context':'context'}
COUNTS={'population','aged_65_plus','households','social_rented','residents_16_plus','employed','areas'}
METRICS={'Age 65+ share':('aged_65_plus','population','aged_65_share'),
         'Social renting share':('social_rented','households','social_rented_share'),
         'Employment share (16+)':('employed','residents_16_plus','employed_share')}


def write(path,obj):
    dest=OUT/path;dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def schema(kind,version='1.0.0'):
    return BASE+f'fabric/item/report/definition/{kind}/{version}/schema.json'


def projection(table,column,measure=False,label=None):
    return {'field':{('Measure' if measure else 'Column'):{'Expression':{'SourceRef':{'Entity':table}},'Property':column}},
            'queryRef':table+'.'+column,'nativeQueryRef':column,'displayName':label or column.replace('_',' ')}


def literal(value):return {'expr':{'Literal':{'Value':value}}}


def build():
    write(Path(NAME+'.pbip'),{'$schema':BASE+'fabric/pbip/pbipProperties/1.0.0/schema.json','version':'1.0',
          'artifacts':[{'report':{'path':NAME+'.Report'}}],'settings':{'enableAutoRecovery':True}})
    write(Path(NAME+'.SemanticModel/definition.pbism'),{'$schema':BASE+'fabric/item/semanticModel/definitionProperties/1.0.0/schema.json','version':'1.0'})
    measures=[]
    for label,(num,den,rate) in METRICS.items():
        measures.append({'name':label,'expression':f'DIVIDE(SUM(Neighbourhoods[{num}]), SUM(Neighbourhoods[{den}]))','formatString':'0.0%'})
        for area,code in [('Liverpool','E08000012'),('England','E92000001')]:
            measures.append({'name':area+' '+label,'expression':f'CALCULATE(MAX(Benchmarks[{rate}]), Benchmarks[area_code] = "{code}")','formatString':'0.0%'})
        measures.append({'name':label+' gap to city (pp)','expression':f'100 * ([{label}] - [Liverpool {label}])','formatString':'+0.0;-0.0;0.0'})
    measures.append({'name':'Selected areas','expression':'COUNTROWS(Neighbourhoods)','formatString':'0'})
    tables=[]
    for table,filename in TABLES.items():
        with (ROOT/f'data/processed/{filename}.csv').open() as f:columns=next(csv.reader(f))
        defs=[];types=[]
        for c in columns:
            dt,mt=('int64','Int64.Type') if c in COUNTS else ('double','type number') if c.endswith(('_share','_pp')) or c in ('latitude','longitude') else ('dateTime','type date') if c in ('census_date','source_retrieved') else ('string','type text')
            col={'name':c,'dataType':dt,'sourceColumn':c,'summarizeBy':'none'}
            if c.endswith('_share'):col['formatString']='0.0%'
            elif c.endswith('_pp'):col['formatString']='+0.0;-0.0;0.0'
            elif c in COUNTS:col['formatString']='#,0'
            elif dt=='dateTime':col['formatString']='dd MMM yyyy'
            if c=='latitude':col['dataCategory']='Latitude'
            if c=='longitude':col['dataCategory']='Longitude'
            defs.append(col);types.append('{"'+c+'", '+mt+'}')
        expr=['let',f'    Source = Csv.Document(File.Contents(DataFolder & "/{filename}.csv"), [Delimiter=",", Columns={len(columns)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
              '    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
              '    Types = Table.TransformColumnTypes(Headers, {'+', '.join(types)+'}, "en-GB")','in','    Types']
        obj={'name':table,'columns':defs,'partitions':[{'name':table,'mode':'import','source':{'type':'m','expression':expr}}]}
        if table=='Neighbourhoods':obj['measures']=measures
        tables.append(obj)
    write(Path(NAME+'.SemanticModel/model.bim'),{'name':NAME,'compatibilityLevel':1550,'model':{
        'culture':'en-GB','defaultPowerBIDataSourceVersion':'powerBI_V3','sourceQueryCulture':'en-GB',
        'expressions':[{'name':'DataFolder','kind':'m','expression':'"C:/liverpool-neighbourhood-insights/data/processed" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'}],
        'tables':tables,'relationships':[]}})
    report=Path(NAME+'.Report')
    write(report/'definition.pbir',{'$schema':BASE+'fabric/item/report/definitionProperties/2.0.0/schema.json','version':'4.0',
          'datasetReference':{'byPath':{'path':'../'+NAME+'.SemanticModel'}}})
    write(report/'definition/version.json',{'$schema':schema('versionMetadata'),'version':'4.0.0'})
    write(report/'definition/report.json',{'$schema':schema('report','2.0.0'),'themeCollection':{},'reportSource':'Default'})
    pages=['overview','comparison']
    write(report/'definition/pages/pages.json',{'$schema':schema('pagesMetadata'),'pageOrder':pages,'activePageName':'overview'})
    counter=0
    def visual(page,typ,title,x,y,w,h,roles=None,text=None):
        nonlocal counter
        counter+=1;name=f'visual{counter:03}'
        v={'visualType':typ,'drillFilterOtherVisuals':True,'visualContainerObjects':{'title':[{'properties':{
            'show':literal('true'),'text':literal("'"+title.replace("'","''")+"'"),'fontSize':literal('12D'),
            'fontColor':{'solid':{'color':literal("'#15333B'")}}}}]}}
        if roles:v['query']={'queryState':{k:{'projections':p} for k,p in roles.items()}}
        if text:
            v['visualContainerObjects']={}
            v['objects']={'general':[{'properties':{'paragraphs':[{'textRuns':[{'value':text,'textStyle':{'fontFamily':'Segoe UI','fontSize':'16pt','color':'#15333B'}}]}]}}]}
        write(report/f'definition/pages/{page}/visuals/{name}/visual.json',{'$schema':schema('visualContainer','2.0.0'),'name':name,
            'position':{'x':x,'y':y,'z':counter,'width':w,'height':h,'tabOrder':counter},'visual':v})
    for p,title in zip(pages,['Liverpool | Census 2021 overview','Area comparison | Census 2021']):
        write(report/f'definition/pages/{p}/page.json',{'$schema':schema('page','2.0.0'),'name':p,'displayName':title,
            'displayOption':'FitToPage','width':1280,'height':800})
        visual(p,'textbox','',25,15,1230,55,text=title)
    for i,label in enumerate(METRICS):
        visual('overview','card','Liverpool: '+label,25+i*415,80,395,115,{'Data':[projection('Neighbourhoods','Liverpool '+label,True)]})
    visual('overview','tableEx','Published benchmarks (each indicator uses its own denominator)',25,215,1230,180,
        {'Values':[projection('Benchmarks',c) for c in ['area_name','population','aged_65_share','social_rented_share','employed_share']]})
    visual('overview','clusteredBarChart','Social renting share by MSOA (scroll to see all areas)',25,420,790,300,
        {'Category':[projection('Neighbourhoods','area_name')],'Y':[projection('Neighbourhoods','Social renting share',True)]})
    visual('overview','textbox','',840,420,415,300,text='61 MSOAs on consistent 2021 boundaries. Employment includes students in work and all residents aged 16+. This is a historical baseline, not current service demand. Open reports/dashboard.html for the offline area map.')
    visual('comparison','slicer','Select statistical area(s)',25,80,1230,95,{'Values':[projection('Neighbourhoods','area_name')]})
    for i,label in enumerate(METRICS):
        visual('comparison','card',label+' | selected areas',25+i*415,195,395,105,{'Data':[projection('Neighbourhoods',label,True)]})
    visual('comparison','tableEx','Area shares and gaps to published Liverpool figures (pp)',25,325,1230,360,
        {'Values':[projection('Neighbourhoods','area_name')]+[projection('Neighbourhoods',name,True) for label in METRICS for name in [label,label+' gap to city (pp)']]})
    visual('comparison','textbox','',25,705,1230,80,text='Cards use summed numerators / summed denominators for the selection. With all 61 selected, small differences from published city figures can arise from Census disclosure control. MSOAs are not current wards.')
    print(f'Built {len(pages)} native report pages, {counter} visuals and {len(measures)} DAX measures. Desktop execution is not verified.')


if __name__=='__main__':build()
