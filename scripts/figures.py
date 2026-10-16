from pathlib import Path
import json,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
R=Path(__file__).resolve().parents[1];D=json.loads((R/'results/analysis.json').read_text(encoding='utf-8'));out=R/'results/figures';out.mkdir(exist_ok=True)
font=Path('C:/Windows/Fonts/malgun.ttf')
if font.exists():font_manager.fontManager.addfont(str(font));plt.rcParams['font.family']=font_manager.FontProperties(fname=str(font)).get_name()
plt.rcParams.update({'axes.unicode_minus':False,'figure.facecolor':'#f2efe7','axes.facecolor':'#f2efe7','axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'#f2efe7'})
T=D['total'];fig,ax=plt.subplots(figsize=(9,4),layout='constrained');rates=[T['rate']*100,T['broad_rate']*100];ax.barh(['생성형 AI 명시','포괄 AI 포함'],rates,color=['#2458ea','#df704c'],height=.5);ax.set(xlim=(0,100),xlabel='관찰 공고 내 비율 (%)',title='자격요건·우대사항의 AI 역량 명시 비율');ax.invert_yaxis()
for i,(k,v) in enumerate(zip([T['genai'],T['broad_ai']],rates)):ax.text(v+1,i,f'{k}/{T["n"]} · {v:.1f}%',va='center')
fig.savefig(out/'ai_requirement_rates.png',dpi=200);fig.savefig(out/'ai_requirement_rates.svg');plt.close(fig)
fig,ax=plt.subplots(figsize=(9,5),layout='constrained')
for i,r in enumerate(D['roles']):
    v=r['rate']*100;l,h=[x*100 for x in r['ci']];ax.errorbar(v,i,xerr=[[v-l],[h-v]],fmt='o',capsize=5,color='#2458ea');ax.text(min(v+3,90),i-.13,f'{r["genai"]}/{r["n"]} · {v:.1f}%',fontsize=10)
ax.set(xlim=(-2,102),yticks=range(4),yticklabels=[r['role'] for r in D['roles']],xlabel='비율 (%) · 선: Wilson 95% 이항모형 참고 구간',title='직무별 생성형 AI 명시 비율');ax.invert_yaxis();fig.text(.04,.01,'편의·기업 군집 표본: 시장 모수의 신뢰구간이 아니며 직무 순위 단정 불가.',fontsize=8);fig.savefig(out/'role_comparison.png',dpi=200);plt.close(fig)
fig,ax=plt.subplots(figsize=(10,5),layout='constrained');x=np.arange(len(D['companies']));n=np.array([r['n'] for r in D['companies']]);k=np.array([r['genai'] for r in D['companies']]);ax.bar(x,k,color='#2458ea',label='생성형 AI 명시');ax.bar(x,n-k,bottom=k,color='#c5ccbc',label='미명시');ax.set(xticks=x,xticklabels=[r['company'] for r in D['companies']],ylabel='분석 공고 수',title='기업 채용페이지별 공고 구성');ax.legend();fig.savefig(out/'company_comparison.png',dpi=200);plt.close(fig);print('Three measured figures and one SVG exported.')
