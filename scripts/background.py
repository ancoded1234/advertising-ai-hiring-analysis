from probe import R
from pathlib import Path
import os,time,requests,json,datetime
def main():
    urls=['https://www.ilo.org/publications/generative-ai-and-jobs-refined-global-index-occupational-exposure','https://www.weforum.org/publications/the-future-of-jobs-report-2025/','https://careers.designfever.com/job-opening/88','https://chai.career.greetinghr.com/ko/o/239857']
    out=[]
    for i,url in enumerate(urls):
        for attempt in range(3):
            r=requests.post('https://api.firecrawl.dev/v2/scrape',headers={'Authorization':'Bearer '+os.environ['FIRECRAWL_API_KEY']},json={'url':url,'formats':['markdown'],'onlyMainContent':True},timeout=100);j=r.json()
            if r.status_code!=429:break
            delay=min(60,max(5,j.get('retry_after_seconds',20)));print('Firecrawl rate limit, retry after',delay,flush=True);time.sleep(delay)
        d=j.get('data',{});meta=d.get('metadata',{});record=dict(url=url,collected_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),method='Firecrawl v2 scrape',http_status=r.status_code,source_status=meta.get('statusCode'),title=meta.get('title'),success=bool(j.get('success')) and meta.get('statusCode')==200,characters=len(d.get('markdown','')))
        (R/f'data/firecrawl/research_{i}_full.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8');out.append(record);print('Firecrawl',i,record['success'],flush=True);time.sleep(6)
    (R/'data/firecrawl/research_sources.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
