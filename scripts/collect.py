"""Collect public employer job pages. No authentication, CAPTCHA solving, or proxies."""
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from urllib.robotparser import RobotFileParser
import requests,json,datetime,time,re,hashlib
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1]
for d in ['data/raw/pages','results','docs/data','docs/assets']:(R/d).mkdir(parents=True,exist_ok=True)
S=requests.Session();S.headers['User-Agent']='AdvertisingHiringResearch/1.0 (educational; public job descriptions only)'
SOURCES=[
 {'name':'에코마케팅','url':'https://echomarketing.career.greetinghr.com/ko/recruit','kind':'greeting'},
 {'name':'차이커뮤니케이션','url':'https://chai.career.greetinghr.com/ko/guide1','kind':'greeting'},
 {'name':'대학내일ES','url':'https://univ.careerlink.kr/jobs','kind':'browser','pattern':r'/jobs/RC\d+'},
 {'name':'디자인피버','url':'https://careers.designfever.com/job-opening','kind':'browser','pattern':r'/job-opening/\d+'},
 {'name':'이노레드','url':'https://beloved.careers.team/job-descriptions','kind':'browser','pattern':r'/job-descriptions/.+'},
 {'name':'TBWA KOREA','url':'https://tbwakorea.com/careers/','kind':'tbwa','pattern':r'/careers/.+'},
]
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,o):(R/p).write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
def allowed(url):
    root=f'{urlsplit(url).scheme}://{urlsplit(url).netloc}';r=S.get(root+'/robots.txt',timeout=25)
    body=r.text;plain='User-agent:' in body or 'user-agent:' in body
    if r.status_code==404:return True,{'status':404,'decision':'robots_absent'}
    if r.status_code!=200 or not plain:return False,{'status':r.status_code,'decision':'robots_unavailable'}
    rp=RobotFileParser();rp.parse(body.splitlines());ok=rp.can_fetch(S.headers['User-Agent'],url)
    return ok,{'status':r.status_code,'decision':'allowed' if ok else 'disallowed','rules':body}
def render(page,url):
    page.goto(url,wait_until='domcontentloaded',timeout=45000);page.wait_for_timeout(1800)
    # Wait for client-rendered lists without accessing private endpoints.
    try:page.wait_for_load_state('networkidle',timeout=12000)
    except Exception:pass
    return page.content(),page.inner_text('body')
def greeting_openings(html):
    n=BeautifulSoup(html,'html.parser').select_one('#__NEXT_DATA__')
    if not n:return []
    j=json.loads(n.get_text());qs=j.get('props',{}).get('pageProps',{}).get('dehydratedState',{}).get('queries',[])
    return next((q['state']['data'] for q in qs if q.get('queryKey')==['openings']),[])
def main():
    manifest=[];jobs=[]
    with sync_playwright() as p:
        browser=p.chromium.launch();page=browser.new_page()
        for source in SOURCES:
            entry=dict(source,collected_at=stamp());print('Source:',source['name'],flush=True)
            try:
                ok,robots=allowed(source['url']);entry['robots']=robots
                if not ok:entry.update(status='skipped_robots');manifest.append(entry);continue
                if source['kind']=='browser':html,text=render(page,source['url']);status=200
                else:
                    r=S.get(source['url'],timeout=35);status=r.status_code;html=r.text;r.raise_for_status();text=BeautifulSoup(html,'html.parser').get_text('\n',strip=True)
                ident=hashlib.sha256(source['url'].encode()).hexdigest()[:14];(R/f'data/raw/pages/{ident}_list.html').write_text(html,encoding='utf-8')
                links=[]
                if source['kind']=='greeting':
                    for item in greeting_openings(html):
                        links.append({'url':urljoin(source['url'],f"/ko/o/{item['openingId']}"),'title':item['title'],'listed_metadata':item})
                else:
                    soup=BeautifulSoup(html,'html.parser')
                    for a in soup.select('a[href]'):
                        url=urljoin(source['url'],a['href'])
                        match=('경력채용' in a.get_text()) if source['kind']=='tbwa' else bool(re.search(source['pattern'],url))
                        if match and url not in [x['url'] for x in links]:links.append({'url':url,'title':a.get_text(' ',strip=True)})
                entry.update(http_status=status,status='collected',listed_jobs=len(links));print('Listed:',len(links),flush=True)
                for item in links:
                    rec=dict(item,company=source['name'],source_list=source['url'],collected_at=stamp(),status='collected')
                    key=hashlib.sha256(item['url'].encode()).hexdigest()[:14];path=R/f'data/raw/pages/{key}.html'
                    try:
                        if item['url'].lower().endswith('.pdf'):
                            import pymupdf
                            path=path.with_suffix('.pdf')
                            if not path.exists():
                                r=S.get(item['url'],timeout=35);r.raise_for_status();path.write_bytes(r.content)
                            with pymupdf.open(path) as pdf:body='\n'.join(page.get_text() for page in pdf)
                            detail=body
                        elif path.exists():detail=path.read_text(encoding='utf-8');body=BeautifulSoup(detail,'html.parser').get_text('\n',strip=True)
                        elif source['kind'] in ['browser']:
                            detail,body=render(page,item['url']);path.write_text(detail,encoding='utf-8')
                        else:
                            time.sleep(.6);r=S.get(item['url'],timeout=35);r.raise_for_status();detail=r.text;path.write_text(detail,encoding='utf-8');body=BeautifulSoup(detail,'html.parser').get_text('\n',strip=True)
                        rec.update(raw_path=str(path.relative_to(R)).replace('\\','/'),text=body,sha256=hashlib.sha256(detail.encode()).hexdigest())
                        if 'Vercel Security Checkpoint' in body or '403 Forbidden' in body:rec['status']='blocked';rec['text']=''
                    except Exception as e:rec.update(status='failed',error=type(e).__name__)
                    jobs.append(rec);save('data/raw/jobs.json',jobs);print('Job:',len(jobs),item['title'][:60],rec['status'],flush=True)
            except Exception as e:entry.update(status='failed',error=type(e).__name__)
            manifest.append(entry);save('results/collection_manifest.json',manifest)
        browser.close()
    save('data/raw/jobs.json',jobs);save('results/collection_manifest.json',manifest);print('DONE',len(jobs),flush=True)
if __name__=='__main__':main()
