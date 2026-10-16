from pathlib import Path
import requests,json,datetime,os
from dotenv import load_dotenv
R=Path(__file__).resolve().parents[1]
for p in [R,*R.parents]:
    if (p/'.env').is_file():load_dotenv(p/'.env',override=False);print('Existing .env loaded:',p/'.env');break
for d in ['data/raw','data/firecrawl','results','docs/assets','docs/data']:(R/d).mkdir(parents=True,exist_ok=True)
def main():
    sources=[];key=os.getenv('FIRECRAWL_API_KEY');print('Firecrawl key configured:',bool(key))
    urls=['https://www.wanted.co.kr/robots.txt','https://www.wanted.co.kr/terms','https://www.jobkorea.co.kr/robots.txt','https://www.saramin.co.kr/robots.txt','https://www.ilo.org/publications/generative-ai-and-jobs-refined-global-index-occupational-exposure','https://www.weforum.org/publications/the-future-of-jobs-report-2025/']
    for i,url in enumerate(urls):
        entry={'url':url,'collected_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'Firecrawl v2 scrape'}
        try:
            r=requests.post('https://api.firecrawl.dev/v2/scrape',headers={'Authorization':f'Bearer {key}'},json={'url':url,'formats':['markdown'],'onlyMainContent':True},timeout=100)
            j=r.json();data=j.get('data',{});entry.update(http_status=r.status_code,source_status=data.get('metadata',{}).get('statusCode'),title=data.get('metadata',{}).get('title'),success=j.get('success',False) and data.get('metadata',{}).get('statusCode')==200)
            (R/f'data/firecrawl/{i}_full.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
            if i<4:print(url,entry, data.get('markdown','')[:3500],flush=True)
            else:print(url,entry,flush=True)
        except Exception as e:entry.update(success=False,error=type(e).__name__)
        sources.append(entry)
    (R/'data/firecrawl/sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
