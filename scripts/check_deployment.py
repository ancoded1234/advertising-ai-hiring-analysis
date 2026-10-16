from pathlib import Path
import json,subprocess,datetime,hashlib,requests
R=Path(__file__).resolve().parents[1];base='https://ancoded1234.github.io/advertising-ai-hiring-analysis/'
meta=json.loads(subprocess.check_output(['gh','api','repos/ancoded1234/advertising-ai-hiring-analysis/pages'],text=True))
assets={}
for path in ['index.html','assets/app.js','assets/style.css','data/analysis.json']:
    r=requests.get(base+path,timeout=30);r.raise_for_status();assert r.content.replace(b'\r\n',b'\n')==(R/'docs'/path).read_bytes().replace(b'\r\n',b'\n'),f'Deployed file differs: {path}'
    assets[path]={'http_status':r.status_code,'sha256':hashlib.sha256(r.content).hexdigest()}
record={'verified_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'url':base,'public_unauthenticated_http':True,'github_pages_status':meta['status'],'source':meta['source'],'assets':assets}
(R/'results/deployment.json').write_text(json.dumps(record,indent=2),encoding='utf-8');print(json.dumps(record,indent=2))
