from pathlib import Path
import json,sys
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];out=R/'test-results';out.mkdir(exist_ok=True);url=sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8766';report=[]
with sync_playwright() as p:
    browser=p.chromium.launch();page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    for w,h in [(1440,900),(1280,720),(768,1024),(390,844)]:
        page.set_viewport_size({'width':w,'height':h});page.goto(url);page.wait_for_selector('.slide.active');page.evaluate('document.fonts.ready')
        for i in range(12):
            page.evaluate('(n)=>{location.hash=String(n)}',i+1);page.wait_for_timeout(420)
            assert page.locator('.slide.active').count()==1;assert page.locator('#page').inner_text()==f'{i+1:02d} / 12'
            dims=page.evaluate('''()=>{const s=document.querySelector('.slide.active'),e=[...s.querySelectorAll('h1,h2,h3,p,table,svg,.hero,.grid,.flow,.dots')],rects=e.map(e=>e.getBoundingClientRect());return {width:innerWidth,docWidth:document.documentElement.scrollWidth,top:Math.min(...rects.map(r=>r.top)),bottom:Math.max(...rects.map(r=>r.bottom)),header:document.querySelector('header').getBoundingClientRect().bottom,footer:document.querySelector('footer').getBoundingClientRect().top}}''')
            if dims['docWidth']>w+2 or dims['top']<dims['header']-1 or dims['bottom']>dims['footer']+2:page.screenshot(path=str(out/f'failure-{w}-{i+1}.png'),full_page=True)
            assert dims['docWidth']<=w+2,('horizontal overflow',i+1,dims)
            assert dims['top']>=dims['header']-1,('header overlap',i+1,dims)
            assert dims['bottom']<=dims['footer']+2,('footer overlap',i+1,dims)
            report.append(dict(height=h,slide=i+1,**dims))
            if w==1440 and i in [0,5,6,8,9]:page.screenshot(path=str(out/f'slide-{i+1:02d}.png'),full_page=True)
            if w==390 and i in [0,6]:page.screenshot(path=str(out/f'mobile-{i+1:02d}.png'),full_page=True)
        page.keyboard.press('Home');assert page.locator('#page').inner_text()=='01 / 12';page.keyboard.press('ArrowRight');assert page.locator('#page').inner_text()=='02 / 12';page.locator('#next').click();assert page.locator('#page').inner_text()=='03 / 12';page.locator('#prev').click();assert page.locator('#page').inner_text()=='02 / 12'
    page.set_viewport_size({'width':1440,'height':900});page.evaluate('location.hash="6"');page.wait_for_timeout(420);page.locator('.slide.active [data-mode="broad"]').click();assert '44.8%' in page.locator('#summary-view').inner_text();page.locator('.slide.active [data-mode="strict"]').click();assert '20.7%' in page.locator('#summary-view').inner_text()
    page.locator('.slide.active [data-posting]').first.click();assert page.locator('#explorer').evaluate('(e)=>e.open');assert page.locator('#rows tr').count()==1;page.locator('#search').fill('');page.locator('#status-filter').select_option('genai');assert page.locator('#rows tr').count()==6;page.locator('#status-filter').select_option('broad');assert page.locator('#rows tr').count()==13;page.locator('#status-filter').select_option('excluded');assert page.locator('#rows tr').count()==16
    with page.expect_download() as info:page.locator('#download').click()
    download=info.value;download.save_as(out/'download.csv');assert len((out/'download.csv').read_text(encoding='utf-8-sig').splitlines())==17
    page.locator('#close-explorer').click();page.locator('#fullscreen').click();page.wait_for_timeout(100);assert page.evaluate('!!document.fullscreenElement');page.evaluate('document.exitFullscreen()');assert not errors,errors;browser.close()
(R/'results/browser_qa.json').write_text(json.dumps({'url':url,'slide_viewport_checks':len(report),'javascript_errors':errors,'controls':'keyboard/buttons/fullscreen/mode_toggle/explorer/CSV passed','layouts':report},indent=2),encoding='utf-8');print('PASS: 48 slide/viewport combinations, navigation, fullscreen, definitions, explorer and CSV.')
