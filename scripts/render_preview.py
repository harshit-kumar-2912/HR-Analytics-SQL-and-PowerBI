"""Export analytical figures from validated CSVs; these are not Power BI screenshots."""
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import MaxNLocator

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/processed'
OUT=ROOT/'docs/figures'
def rows(name):
    with (DATA/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m=json.loads((DATA/'metrics.json').read_text())
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','figure.facecolor':'#f5f8fc','axes.facecolor':'#f5f8fc'})
    color='#176b87';accent='#e99d45'
    fig,axs=plt.subplots(2,2,figsize=(14,9),layout='constrained')
    fig.suptitle(f'HR WORKFORCE ANALYTICS | Harshit Kumar\nAs of {m["as_of_date"]} · {m["active_employees"]:,} active employees · {m["terminated_employees"]:,} completed exits',fontsize=17,fontweight='bold')
    for ax,name,title in [(axs[0,0],'gender_distribution.csv','Active workforce by gender'),(axs[0,1],'location_distribution.csv','Active workforce by work location'),(axs[1,1],'age_group_distribution.csv','Active workforce by age group')]:
        data=rows(name);labels=[r['category'] for r in data];values=[int(r['employee_count']) for r in data]
        bars=ax.bar(labels,values,color=color,width=.65);ax.bar_label(bars,fmt='{:,.0f}',padding=4);ax.set_title(title,pad=20);ax.set_ylim(0,max(values)*1.2)
        ax.set_ylabel('Employees')
    annual=rows('annual_workforce.csv');axs[1,0].plot([int(r['year']) for r in annual],[int(r['closing_headcount']) for r in annual],color=color,linewidth=3)
    axs[1,0].set_title('Year-end active headcount');axs[1,0].set_xlabel('Calendar year');axs[1,0].set_ylabel('Employees')
    axs[1,0].xaxis.set_major_locator(MaxNLocator(integer=True,nbins=6))
    fig.supxlabel('Reproducible analytical preview from validated exports · Not a Power BI screenshot',fontsize=9)
    fig.savefig(OUT/'workforce_overview.png',dpi=160)
    other,axes=plt.subplots(1,2,figsize=(14,8),layout='constrained')
    other.suptitle('RETENTION AND DATA QUALITY | Harshit Kumar\nCumulative exit share is not an annual turnover rate',fontsize=17,fontweight='bold')
    depts=sorted(rows('department_exit_share.csv'),key=lambda r:float(r['cumulative_exit_share']))
    bars=axes[0].barh([r['department'] for r in depts],[100*float(r['cumulative_exit_share']) for r in depts],color=color)
    axes[0].bar_label(bars,fmt='%.2f%%',padding=3);axes[0].set_xlim(0,max(100*float(r['cumulative_exit_share']) for r in depts)*1.3)
    axes[0].set_title('Completed exits ÷ eligible hires, by department');axes[0].set_xlabel('Cumulative exit share (%)')
    axes[1].axis('off')
    notes=[('REPORTING DATE',m['as_of_date']),('RAW RECORDS',f'{m["raw_records"]:,}'),('EXCLUDED: INVALID DATE ORDER',str(m['invalid_records'])),
        ('ELIGIBLE HIRES',f'{m["eligible_records"]:,}'),('CUMULATIVE EXIT SHARE',f'{m["cumulative_exit_share"]:.2%}'),
        ('AVERAGE COMPLETED TENURE',f'{m["average_completed_tenure_years"]:.2f} years'),('FUTURE EXIT DATES IN RAW DATA',f'{m["future_termination_records"]:,}'),
        ('AGE AT HIRE <16: REVIEW FLAG',f'{m["hired_under_16_records"]:,} records')]
    for i,(label,value) in enumerate(notes):
        y=.98-i*.117;axes[1].text(.06,y,label,color='#506074',fontsize=10,transform=axes[1].transAxes);axes[1].text(.06,y-.045,value,color=color,fontsize=17,fontweight='bold',transform=axes[1].transAxes)
    other.supxlabel('Exploratory portfolio dataset · Source provenance unverified · No causal or real-company claims',fontsize=9)
    other.savefig(OUT/'retention_quality.png',dpi=160)
    with PdfPages(ROOT/'docs/HR_Analytics_Summary.pdf') as pdf:pdf.savefig(fig);pdf.savefig(other)
    plt.close('all')

if __name__=='__main__':main()
