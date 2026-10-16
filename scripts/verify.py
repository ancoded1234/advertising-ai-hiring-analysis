from pathlib import Path
import json,sys,subprocess
import pandas as pd
from dotenv import dotenv_values
from analyze import broad,terms,split_sections,classify_role
R=Path(__file__).resolve().parents[1];D=json.loads((R/'results/analysis.json').read_text(encoding='utf-8'));rows=D['postings'];inc=[r for r in rows if r['included']];T=D['total'];csv=pd.read_csv(R/'results/coded_postings.csv')
assert len({r['url'] for r in rows})==len(rows);assert len(inc)==T['n']==29;assert sum(r['genai'] for r in inc)==T['genai']==6;assert sum(r['broad_ai'] for r in inc)==T['broad_ai']==13;assert all(r['broad_ai'] for r in inc if r['genai']);assert all(r['section_complete'] for r in inc)
assert T['required']+T['preferred']-T['both']==T['genai'];assert sum(r['n'] for r in D['roles'])==T['n'];assert sum(r['n'] for r in D['companies'])==T['n'];assert int(csv.included.sum())==T['n'];assert json.loads((R/'docs/data/analysis.json').read_text(encoding='utf-8'))==D
assert not broad('Figma, Adobe Creative S(Ai, Ps 등)');assert broad('AI를 활용해 새로운 가능성을 탐구하는 분');assert not terms('AI를 활용해 새로운 가능성을 탐구하는 분');assert terms('생성형 AI 업무 도구 경험');assert terms('GPTs 에이전트 개발')
s,_=split_sections('회사소개\nChatGPT 서비스 회사\n자격요건\n브랜드 디자인 경험\n우대사항\n커뮤니케이션\n주요업무\nMidjourney 제작');assert not terms(s['required']+s['preferred']);assert classify_role('BX 오프라인 프로모션 담당자')[0]=='AE/기획';assert classify_role('팀장 (AE경력 7년)')[0]=='AE/기획';assert classify_role('모션디자이너')[0]=='디자인/영상'
for r in rows:assert all(len(e['text'].split())<=11 for e in r['evidence'])
fire=json.loads((R/'data/firecrawl/research_sources.json').read_text(encoding='utf-8'));assert len(fire)==4 and all(x['success'] and x['source_status']==200 for x in fire)
secrets=[]
for parent in [R,*R.parents]:
    if (parent/'.env').exists():secrets=[v for v in dotenv_values(parent/'.env').values() if v and len(v)>15];break
files=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard'],cwd=R,text=True).splitlines()
for f in files:
    assert not f.startswith('data/raw/') and '_full.json' not in f and not f.endswith('.env')
    p=R/f
    if p.is_file():assert not any(v.encode() in p.read_bytes() for v in secrets),'Secret detected in publishable file'
result={'unique_source_urls':len(rows),'included':len(inc),'genai':T['genai'],'broad_ai':T['broad_ai'],'cross_file_totals':'passed','section_boundary_regression':'passed','Illustrator_false_positive_regression':'passed','role_lexicon_regressions':'passed','firecrawl_valid_sources':len(fire),'secret_scan':'passed','independent_human_ground_truth':'not available; no classification accuracy claimed'}
(R/'results/data_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False))
