from pathlib import Path
import json,re,hashlib,unicodedata,datetime,math
import pandas as pd
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parents[1];ROLES=['AE/기획','카피라이터','디자인/영상','퍼포먼스'];NOW=datetime.datetime.now(datetime.timezone.utc)
TOOLS={
 'ChatGPT/GPT':r'chat\s*gpt|챗\s*(?:gpt|지피티)|\bgpts?(?:-?\d[\w.-]*)?\b',
 'Midjourney':r'mid\s*journey|미드\s*저니',
 'Stable Diffusion':r'stable\s*diffusion|스테이블\s*디퓨전|comfy\s*ui|컴피\s*유아이',
 'Runway':r'\brunway(?:ml)?\b|런웨이',
 'Claude':r'\bclaude\b|클로드', 'Gemini':r'\bgemini\b|제미나이|제미니',
 'DALL·E':r'dall[\s·-]*e', 'Firefly':r'\bfirefly\b|파이어플라이',
 'Nano Banana':r'nano\s*banana|나노\s*바나나','Higgsfield':r'higgsfield|힉스필드',
 'Kling':r'\bkling\b|클링', 'Sora':r'\bsora\b',
 'Copilot':r'\bcopilot\b|코파일럿','Perplexity':r'perplexity|퍼플렉시티',
 '생성형 AI':r'생성형\s*(?:ai|인공\s*지능)|생성\s*ai|generative\s*ai|\bgen\s*ai\b',
}
def clean(s):return re.sub(r'[\u200b-\u200f\ufeff]','',unicodedata.normalize('NFKC',s)).replace('\xa0',' ').strip()
def html_text(html):
    s=BeautifulSoup(html,'lxml');blocks=[]
    for e in s.find_all(['p','li','h1','h2','h3','h4','h5','h6']):
        if e.find_parent(['p','li','h1','h2','h3','h4','h5','h6']):continue
        t=clean(e.get_text(' ',strip=True))
        if t:blocks.append(t)
    return '\n'.join(blocks) if blocks else s.get_text('\n',strip=True)
def normalize_title(rec,soup):
    if rec['company']=='디자인피버':
        h=soup.select_one('.job-title')
        if h and h.get_text(strip=True):return clean(h.get_text(' ',strip=True))
    title=rec['title'];title=re.split(r'\s(?:경력\s|신입\s*\||정규직\s|무관\s*\|)',title)[0]
    return clean(title)
def classify_role(title):
    t=title.lower()
    if re.search(r'인재풀|상시\s*지원\s*희망|talent\s*pool|junior board',t):return None,'talent_pool_or_non_job'
    if re.search(r'엔지니어|fde|데이터\s*분석|staff|총무|재무|fp&a|자금|퍼블리셔|솔루션\s*기획|웹기획|seo\s*/?\s*geo',t):return None,'outside_four_roles'
    if re.search(r'카피라이터|카피\s*라이터|copywriter|\bcw\b',t):return '카피라이터',None
    if re.search(r'퍼포먼스|performance|그로스|growth|crm',t):return '퍼포먼스',None
    if re.search(r'디자이너|디자인|designer|영상|(?<!프로)모션|비주얼\s*디렉터|비주얼디렉터|\bvd\b|아트\s*디렉터',t):return '디자인/영상',None
    if re.search(r'(?<![a-z])ae(?![a-z])|기획|마케터|마케팅|marketer|프로모션|매체\s*매니지먼트|이커머스\s*매니저',t):return 'AE/기획',None
    return None,'outside_four_roles'
def section_kind(line):
    compact=re.sub(r'[^a-zA-Z가-힣]','',line).lower()
    if len(line)>90:return None
    if re.search(r'우대사항|우대요건|우대조건|이런경험이있으면더좋|이런경험이있다면|이런분이면더좋|preferred|nicetohave',compact):return 'preferred'
    if re.search(r'지원자격|자격요건|기본요건|필수요건|필수조건|필수사항|자격사항|이런동료를찾|이런팀원을찾|이런분을찾|이런분을모십|qualifications|requirements|aboutyou|whoyouare|whowillthriveinthisrole',compact):return 'required'
    if compact in ['thework','applicationdocuments']:return 'other'
    if re.search(r'주요업무|담당업무|주요역할|이런일을|이런업무를|채용절차|채용프로세스|근무조건|급여사항|복리후생|지원방법|입사후|리더의한마디|동료의한마디|채용정보|근무여건|전형절차|함께하는과정|공유하기|지원하기|서류접수|회사소개|기타사항|responsibilities|howtoapply|benefits|채용공고목록',compact):return 'other'
    return None
def split_sections(text):
    out={'required':[],'preferred':[],'other':[]};headings=[];state='other'
    for raw in text.splitlines():
        line=clean(raw)
        if not line:continue
        kind=section_kind(line)
        if kind:state=kind;headings.append({'heading':line,'kind':kind});continue
        if line not in out[state]:out[state].append(line)
    return {k:'\n'.join(v) for k,v in out.items()},headings
def terms(s):return [name for name,p in TOOLS.items() if re.search(p,s,re.I)]
def broad(s):
    # Adobe Illustrator's Ai is not artificial intelligence.
    sanitized=re.sub(r'\bai(?=\s*[,/]\s*ps\b)','',s,flags=re.I)
    return bool(terms(sanitized) or re.search(r'(?<![a-z])ai(?![a-z])|인공\s*지능',sanitized,re.I))
def ci(k,n):
    if not n:return [None,None]
    z=1.959963984540054;v=k/n;den=1+z*z/n;mid=(v+z*z/(2*n))/den;delta=z*math.sqrt(v*(1-v)/n+z*z/(4*n*n))/den;return [mid-delta,mid+delta]
def save(path,obj):(R/path).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
    records=json.loads((R/'data/raw/jobs.json').read_text(encoding='utf-8'));out=[];seen=set();reviews=[]
    ocrpath=R/'data/raw/ocr.json';ocr=json.loads(ocrpath.read_text(encoding='utf-8')) if ocrpath.exists() else {}
    for rec in records:
        row={k:rec.get(k) for k in ['url','company','source_list','collected_at','status','raw_path']};row['id']=hashlib.sha256(rec['url'].encode()).hexdigest()[:12];text=rec.get('text','');title=rec['title'];due=None
        if rec.get('raw_path','').endswith('.html'):
            soup=BeautifulSoup((R/rec['raw_path']).read_text(encoding='utf-8'),'lxml');title=normalize_title(rec,soup);node=soup.select_one('#__NEXT_DATA__')
            if node:
                j=json.loads(node.get_text());qs=j.get('props',{}).get('pageProps',{}).get('dehydratedState',{}).get('queries',[])
                q=next((q for q in qs if 'getOpeningById' in q.get('queryKey',[])),None)
                if q:
                    info=q['state']['data']['data']['openingsInfo'];text=html_text(info['detail']);title=info['title'];due=info.get('dueDate')
        if rec['url'] in ocr:text=ocr[rec['url']]['text'];row['ocr']=True
        else:row['ocr']=False
        text=clean(text);row.update(title=title,due_date=due);role,excluded=classify_role(title);row['role']=role
        if rec['status']!='collected':excluded='fetch_failed'
        elif '접수마감' in rec['title'] or (due and datetime.datetime.fromisoformat(due.replace('Z','+00:00'))<NOW):excluded='closed'
        elif rec['url'] in seen:excluded='duplicate_url'
        seen.add(rec['url']);sections,headings=split_sections(text)
        complete=bool(sections['required'] and any(h['kind']=='required' for h in headings))
        if not excluded and not complete:excluded='unreadable_qualification_section'
        req=terms(sections['required']);pref=terms(sections['preferred']);allterms=terms(text);g=bool(req or pref);b=broad(sections['required']+'\n'+sections['preferred'])
        evidence=[]
        for section in ['required','preferred']:
            for line in sections[section].splitlines():
                found=terms(line)
                if found or broad(line):evidence.append(dict(section=section,terms=found,text=line))
        row.update(included=excluded is None,exclusion_reason=excluded,section_complete=complete,genai=g,broad_ai=b,required_genai=bool(req),preferred_genai=bool(pref),required_broad=broad(sections['required']),preferred_broad=broad(sections['preferred']),anywhere_genai=bool(allterms),tools=sorted(set(req+pref)),anywhere_tools=allterms,evidence=evidence)
        out.append(row);reviews.append(dict(id=row['id'],company=rec['company'],title=title,url=rec['url'],included=row['included'],exclusion_reason=excluded,role=role,headings=headings,sections=sections,evidence=evidence))
    save('data/raw/section_review.json',reviews)
    # Optional evidence-backed manual review decisions are applied before aggregating.
    overrides=R/'data/review_decisions.json'
    if overrides.exists():
        decisions=json.loads(overrides.read_text(encoding='utf-8'))
        for row in out:
            if row['id'] in decisions:
                decision=decisions[row['id']];row.update(decision['changes']);row['review_note']=decision['reason']
    inc=[r for r in out if r['included']];n=len(inc)
    def summary(rows):
        n=len(rows);k=sum(r['genai'] for r in rows);b=sum(r['broad_ai'] for r in rows)
        return dict(n=n,genai=k,rate=k/n if n else None,broad_ai=b,broad_rate=b/n if n else None,required=sum(r['required_genai'] for r in rows),preferred=sum(r['preferred_genai'] for r in rows),both=sum(r['required_genai'] and r['preferred_genai'] for r in rows),required_broad=sum(r['required_broad'] for r in rows),preferred_broad=sum(r['preferred_broad'] for r in rows),ci=ci(k,n),broad_ci=ci(b,n))
    group=[dict(role=g,**summary([r for r in inc if r['role']==g])) for g in ROLES];companies=[dict(company=g,**summary([r for r in inc if r['company']==g])) for g in dict.fromkeys(r['company'] for r in out)]
    tools=[dict(tool=t,jobs=sum(t in r['tools'] for r in inc),anywhere_jobs=sum(t in r['anywhere_tools'] for r in inc)) for t in TOOLS];tools.sort(key=lambda x:-x['jobs'])
    from collections import Counter
    audit=dict(collected_at=NOW.isoformat(),listed_records=len(out),unique_urls=len(set(r['url'] for r in out)),included=n,excluded=dict(Counter(r['exclusion_reason'] for r in out if not r['included'])),companies_in_sample=len({r['company'] for r in inc}),unreadable=sum(r['exclusion_reason']=='unreadable_qualification_section' for r in out),anywhere_genai=sum(r['anywhere_genai'] for r in inc),genai_only_elsewhere=sum(r['anywhere_genai'] and not r['genai'] for r in inc))
    sensitivity=[dict(excluded_company=c['company'],**summary([r for r in inc if r['company']!=c['company']])) for c in companies if c['n']]
    public=[]
    for row in out:
        item=dict(row);evidence=[]
        for e in row['evidence'][:1]:
            text=e['text'];positions=[m.start() for p in TOOLS.values() for m in re.finditer(p,text,re.I)]
            pos=min(positions) if positions else max(0,text.lower().find('ai'));window=text[max(0,pos-25):];excerpt=' '.join(window.split()[:10])[:110]
            evidence.append(dict(e, text=excerpt+'…' if excerpt!=text else excerpt))
        item['evidence']=evidence;public.append(item)
    audit['ocr_postings']=sum(r['ocr'] for r in inc);audit['manual_review_decisions']=len(decisions) if overrides.exists() else 0
    report=dict(audit=audit,total=summary(inc),roles=group,companies=companies,tools=tools,leave_one_company_out=sensitivity,postings=public,collection=json.loads((R/'results/collection_manifest.json').read_text(encoding='utf-8')))
    save('results/analysis.json',report);save('docs/data/analysis.json',report)
    flat=[]
    for r in out:
        row={k:v for k,v in r.items() if k not in ['evidence','tools','anywhere_tools']};row['tools']='; '.join(r['tools']);row['evidence_sections']='; '.join(sorted({e['section'] for e in r['evidence']}));flat.append(row)
    pd.DataFrame(flat).to_csv(R/'results/coded_postings.csv',index=False,encoding='utf-8-sig');pd.DataFrame(group).to_csv(R/'results/role_summary.csv',index=False);pd.DataFrame(companies).to_csv(R/'results/company_summary.csv',index=False);pd.DataFrame(tools).to_csv(R/'results/tool_counts.csv',index=False)
    print(json.dumps({'audit':audit,'total':report['total'],'roles':group,'companies':companies},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
