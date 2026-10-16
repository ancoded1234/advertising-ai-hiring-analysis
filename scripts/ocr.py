"""Read image-only public job descriptions with Windows Korean OCR; cache originals locally."""
from pathlib import Path
import json,requests,hashlib,asyncio
from bs4 import BeautifulSoup
from PIL import Image
from winrt.windows.media.ocr import OcrEngine
from winrt.windows.globalization import Language
from winrt.windows.storage import StorageFile,FileAccessMode
from winrt.windows.graphics.imaging import BitmapDecoder,SoftwareBitmap,BitmapPixelFormat
R=Path(__file__).resolve().parents[1]
async def main():
    engine=OcrEngine.try_create_from_language(Language('ko'));assert engine,'Korean Windows OCR language pack required'
    jobs=json.loads((R/'data/raw/jobs.json').read_text(encoding='utf-8'));out={}
    cache=R/'data/raw/ocr.json'
    if cache.exists():out=json.loads(cache.read_text(encoding='utf-8'))
    for row in jobs:
        if not row.get('raw_path','').endswith('.html'):continue
        soup=BeautifulSoup((R/row['raw_path']).read_text(encoding='utf-8'),'html.parser');node=soup.select_one('#__NEXT_DATA__')
        if not node:continue
        qs=json.loads(node.get_text()).get('props',{}).get('pageProps',{}).get('dehydratedState',{}).get('queries',[]);q=next((q for q in qs if 'getOpeningById' in q.get('queryKey',[])),None)
        if not q:continue
        html=q['state']['data']['data']['openingsInfo']['detail'];detail=BeautifulSoup(html,'html.parser')
        if len(detail.get_text(' ',strip=True))>50:continue
        if row['url'] in out:continue
        all_lines=[];images=[]
        for i,img in enumerate(detail.select('img[src]')):
            url=img['src'];key=hashlib.sha256(url.encode()).hexdigest()[:14];path=R/f'data/raw/pages/{key}.jpg'
            if not path.exists():
                res=requests.get(url,timeout=30);res.raise_for_status();path.write_bytes(res.content)
            with Image.open(path) as source:
                im=source.convert('RGB');w,h=im.size;parts=[]
                for y in range(0,h,2900):
                    tile=im.crop((0,max(0,y-50),w,min(h,y+2950)));tile.thumbnail((3500,3500));tilepath=R/f'data/raw/pages/{key}_{y}.png';tile.save(tilepath)
                    file=await StorageFile.get_file_from_path_async(str(tilepath.resolve()));stream=await file.open_async(FileAccessMode.READ);decoder=await BitmapDecoder.create_async(stream);bitmap=await decoder.get_software_bitmap_async();bitmap=SoftwareBitmap.convert(bitmap,BitmapPixelFormat.BGRA8);result=await engine.recognize_async(bitmap)
                    lines=[line.text for line in result.lines];parts.extend(lines)
                all_lines.extend(parts);images.append(dict(url=url,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),width=w,height=h))
        out[row['url']]={'engine':'Windows.Media.Ocr / ko','images':images,'text':'\n'.join(all_lines),'lines':all_lines}
        cache.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print('OCR:',row['title'],len(all_lines),'lines',flush=True)
if __name__=='__main__':asyncio.run(main())
