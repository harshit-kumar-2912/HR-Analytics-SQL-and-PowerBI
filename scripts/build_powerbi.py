"""Generate an editable PBIP report and semantic model from the corrected exports."""
import argparse
import copy
import json
import uuid
from pathlib import Path
from pipeline import ROOT

def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')

def build(data_folder='C:/HR-Analytics-SQL-and-PowerBI/data/processed'):
    base=ROOT/'powerbi'
    semantic=base/'HR.SemanticModel'
    report=base/'HR.Report'
    dump(base/'HR.pbip',{'version':'1.0','artifacts':[{'report':{'path':'HR.Report'}}],'settings':{'enableAutoRecovery':True}})
    dump(semantic/'definition.pbism',{'version':'1.0','settings':{}})
    dump(report/'definition.pbir',{'version':'1.0','datasetReference':{'byPath':{'path':'../HR.SemanticModel'}}})
    types={'emp_id':'string','birthdate':'dateTime','hire_date':'dateTime','termdate':'dateTime','gender':'string','race':'string',
        'department':'string','jobtitle':'string','location':'string','location_city':'string','location_state':'string',
        'age':'int64','age_group':'string','status':'string','is_valid':'int64','is_eligible':'int64','quality_issue':'string',
        'hired_under_16':'int64','as_of_date':'dateTime'}
    def column(name,kind):
        out=dict(name=name,dataType=kind,sourceColumn=name,summarizeBy='none')
        if kind=='dateTime':out['formatString']='yyyy-MM-dd'
        return out
    mtypes={'string':'type text','dateTime':'type date','int64':'Int64.Type','double':'type number'}
    def partition(name,filename,cols,eligible=False):
        pairs=', '.join('{"'+k+'", '+mtypes[v]+'}' for k,v in cols.items())
        lines=['let',f'    Source = Csv.Document(File.Contents(DataFolder & "/{filename}"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
            '    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
            '    EmptyDates = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, '+json.dumps([k for k,v in cols.items() if v=='dateTime']).replace('[','{').replace(']','}')+'),',
            '    Typed = Table.TransformColumnTypes(EmptyDates, {'+pairs+'}, "en-US")'+(',' if eligible else ''),]
        if eligible:lines.append('    Eligible = Table.SelectRows(Typed, each [is_eligible] = 1)')
        lines+=['in','    '+('Eligible' if eligible else 'Typed')]
        return dict(name=name,mode='import',source=dict(type='m',expression=lines))
    measures=[
        ('Active Employees','CALCULATE(COUNTROWS(Employees), Employees[status] = "Active")','#,0'),
        ('Eligible Hires','COUNTROWS(Employees)','#,0'),
        ('Terminated Employees','CALCULATE(COUNTROWS(Employees), Employees[status] = "Terminated")','#,0'),
        ('Cumulative Exit Share','DIVIDE([Terminated Employees], [Eligible Hires])','0.00%'),
        ('Average Completed Tenure','AVERAGEX(FILTER(Employees, Employees[status] = "Terminated"), DIVIDE(DATEDIFF(Employees[hire_date], Employees[termdate], DAY), 365.2425))','0.00'),
        ('Closing Headcount',"VAR Y = SELECTEDVALUE('Year'[year]) VAR Cutoff = MIN(DATE(Y, 12, 31), MAXX(ALL(Employees), Employees[as_of_date])) RETURN IF(NOT ISBLANK(Y), CALCULATE(COUNTROWS(Employees), FILTER(Employees, Employees[hire_date] <= Cutoff && (ISBLANK(Employees[termdate]) || Employees[termdate] > Cutoff))))",'#,0'),
        ('Annual Hires',"VAR Y = SELECTEDVALUE('Year'[year]) RETURN COUNTROWS(FILTER(Employees, YEAR(Employees[hire_date]) = Y))",'#,0'),
        ('Annual Exits',"VAR Y = SELECTEDVALUE('Year'[year]) VAR Cutoff = MAXX(ALL(Employees), Employees[as_of_date]) RETURN COUNTROWS(FILTER(Employees, NOT ISBLANK(Employees[termdate]) && YEAR(Employees[termdate]) = Y && Employees[termdate] <= Cutoff))",'#,0'),
    ]
    yearcols={'year':'int64','opening_headcount':'int64','hires':'int64','terminations':'int64','net_change':'int64','closing_headcount':'int64','annual_turnover_rate':'double'}
    model=dict(name='HR Analytics',compatibilityLevel=1567,model=dict(culture='en-US',defaultPowerBIDataSourceVersion='powerBI_V3',
        sourceQueryCulture='en-US',expressions=[dict(name='DataFolder',kind='m',expression=json.dumps(data_folder)+' meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]')],
        tables=[dict(name='Employees',columns=[column(k,v) for k,v in types.items()],partitions=[partition('Employees','employees.csv',types,True)],
            measures=[dict(name=n,expression=e,formatString=f) for n,e,f in measures]),
            dict(name='Year',columns=[column(k,v) for k,v in yearcols.items()],partitions=[partition('Year','annual_workforce.csv',yearcols)])]))
    dump(semantic/'model.bim',model)
    (base/'measures.dax').write_text('\n\n'.join(n+' =\n'+e for n,e,f in measures)+'\n',encoding='utf-8')
    def field(prop,measure=False,table='Employees'):
        expr={'Expression':{'SourceRef':{'Source':'e' if table=='Employees' else 'y'}},'Property':prop}
        return {('Measure' if measure else 'Column'):expr,'Name':table+'.'+prop,'NativeReferenceName':prop}
    def visual(kind,title,x,y,w,h,category=None,measure='Active Employees',series=None,cat_table='Employees'):
        fields=[];roles={}
        if category:
            fields.append(field(category,table=cat_table));roles['Category']=[{'queryRef':fields[-1]['Name'],'active':True}]
        if kind=='tableEx':
            fields=[field(category,table=cat_table),field(measure,True)]
            roles={'Values':[{'queryRef':f['Name']} for f in fields]}
        elif kind=='slicer':
            fields=[field(category,table=cat_table)];roles={'Values':[{'queryRef':fields[0]['Name']}]}
        else:
            fields.append(field(measure,True));roles['Values' if kind=='card' else 'Y']=[{'queryRef':fields[-1]['Name']}]
        if series:
            fields.append(field(series));roles['Series']=[{'queryRef':fields[-1]['Name']}]
        sources=[{'Name':'e','Entity':'Employees','Type':0}]
        if cat_table=='Year':sources.append({'Name':'y','Entity':'Year','Type':0})
        q={'Version':2,'From':sources,'Select':fields}
        if category and kind not in ['slicer','tableEx']:
            q['OrderBy']=[{'Direction':1,'Expression':{'Column':copy.deepcopy(fields[0]['Column'])}}]
        binding={'Primary':{'Groupings':[{'Projections':list(range(len(fields)-(1 if series else 0)))}]},'DataReduction':{'DataVolume':4,'Primary':{'Window':{'Count':1000}}},'Version':1}
        if series:
            binding['Secondary']={'Groupings':[{'Projections':[len(fields)-1]}]}
            binding['DataReduction']['Secondary']={'Top':{'Count':60}}
        if kind=='card':binding={'Primary':{'Groupings':[{'Projections':[0]}]},'DataReduction':{'DataVolume':3,'Primary':{'Top':{}}},'Version':1}
        sv={'visualType':kind,'projections':roles,'prototypeQuery':q,'drillFilterOtherVisuals':True,
            'vcObjects':{'title':[{'properties':{'show':{'expr':{'Literal':{'Value':'true'}}},'text':{'expr':{'Literal':{'Value':"'"+title+"'"}}}}}]}}
        config={'name':uuid.uuid5(uuid.NAMESPACE_DNS,title).hex[:20],'layouts':[{'id':0,'position':{'x':x,'y':y,'z':1000,'width':w,'height':h}}],'singleVisual':sv}
        return {'x':x,'y':y,'z':1000,'width':w,'height':h,'config':json.dumps(config),'filters':'[]',
            'query':json.dumps({'Commands':[{'SemanticQueryDataShapeCommand':{'Query':q,'Binding':binding,'ExecutionMetricsKind':1}}]}),
            'dataTransforms':json.dumps({'objects':{},'projectionOrdering':{k:[fields.index(next(f for f in fields if f['Name']==v['queryRef'])) for v in vals] for k,vals in roles.items()}})}
    def textbox(text):
        config={'name':uuid.uuid5(uuid.NAMESPACE_DNS,text).hex[:20],'layouts':[{'id':0,'position':{'x':10,'y':0,'z':0,'width':1260,'height':55}}],
            'singleVisual':{'visualType':'textbox','objects':{'general':[{'properties':{'paragraphs':[{'textRuns':[{'value':text,'textStyle':{'fontSize':'18pt','fontFamily':'Segoe UI'}}]}]}}]}}}
        return {'x':10,'y':0,'z':0,'width':1260,'height':55,'config':json.dumps(config),'filters':'[]'}
    first=[textbox('HR Workforce Overview | Harshit Kumar | As of 31 Dec 2020'),
        visual('card','Active employees',10,60,250,110),visual('card','Completed tenure of exited employees (years)',270,60,400,110,measure='Average Completed Tenure'),
        visual('slicer','Department',920,60,350,110,category='department'),
        visual('columnChart','Active workforce by gender',10,180,390,240,category='gender'),
        visual('donutChart','Active workforce: headquarters vs remote',410,180,390,240,category='location'),
        visual('clusteredBarChart','Active workforce by state',810,180,460,240,category='location_state'),
        visual('lineChart','Year-end active headcount (calendar year)',10,440,625,260,category='year',measure='Closing Headcount',cat_table='Year'),
        visual('clusteredBarChart','Active workforce by race / ethnicity',645,440,625,260,category='race')]
    second=[textbox('Demographics and Retention | Harshit Kumar | As of 31 Dec 2020'),
        visual('card','Eligible hires to reporting date',10,60,290,110,measure='Eligible Hires'),
        visual('card','Completed exits to reporting date',310,60,290,110,measure='Terminated Employees'),
        visual('card','Cumulative exit share (not annual turnover)',610,60,390,110,measure='Cumulative Exit Share'),
        visual('columnChart','Active workforce by age group',10,180,625,240,category='age_group'),
        visual('clusteredColumnChart','Active age distribution by gender',645,180,625,240,category='age_group',series='gender'),
        visual('tableEx','Department cumulative exit share',10,440,500,260,category='department',measure='Cumulative Exit Share'),
        visual('clusteredColumnChart','Active workforce: department and gender',520,440,750,260,category='department',series='gender')]
    layout={'id':0,'resourcePackages':[],'sections':[{'id':i,'name':f'ReportSection{i}','displayName':n,'filters':'[]','ordinal':i,'visualContainers':v,'config':'{}','displayOption':1,'width':1280,'height':720} for i,(n,v) in enumerate([('Workforce Overview',first),('Demographics and Retention',second)])],
        'config':json.dumps({'version':'5.67','activeSectionIndex':0,'defaultDrillFilterOtherVisuals':True,'settings':{'useNewFilterPaneExperience':True}}),'layoutOptimization':0}
    dump(report/'report.json',layout)
    print('Generated Power BI project. Desktop open/refresh still requires validation.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-folder',default='C:/HR-Analytics-SQL-and-PowerBI/data/processed')
    build(p.parse_args().data_folder)
