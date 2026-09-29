"""按按钮语义检查全部评审场景及弹窗；只检查本地设计原型。"""
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json, os, shutil, threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
SCENES = ['chat','drawer','conversation','work','discover','tasks','me','settings',
          'general','appearance','model','model-providers','model-detail','model-fetch',
          'model-editor','skills-import','agents-import','plugins-import','agents',
          'plugins','mcp','skills','memory','commands','hooks','usage','search','detail']
READ_BUTTONS = '''() => [...document.querySelectorAll('button')].filter(e=>e.checkVisibility()).map(e=>{
 const style=getComputedStyle(e),r=e.getBoundingClientRect();
 const square=e.matches('.icon-button,.composer-send,.foot-icon,.composer-attachment button');
 const medium=e.matches('.solid-button,.outline-button,.soft-button,.text-button,.mini-button,.chip,.composer-mini,.sidebar-action,.sidebar-search,.phone-prompt,.space-switch,.z-back,.segment>button,.import-tabs>button,.suggestions>button');
 const structural=e.matches('.toggle,.nav-link,.side-row,.settings-row,.z-nav-item,.z-config-main,.theme-option,.mw-provider,.provider-choice,.card,.recent-item,.scrim,.bottom-nav button,.settings-menu button,.sidebar-footer button,.pad-quick-row,.pad-agent-row,.pad-master-item,.model-option,.file-row');
 return {action:e.dataset.action||'',text:e.innerText.trim(),classes:e.className,kind:square?'icon':medium?'medium':structural?'structural':'UNCLASSIFIED',height:r.height,width:r.width,font:style.fontSize,line:style.lineHeight,padding:style.padding,clipped:e.scrollWidth>e.clientWidth+1};
})'''

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass

def main():
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    url=f'http://127.0.0.1:{server.server_port}'
    rows, failures, errors = [], [], []
    mac=Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    chrome=os.environ.get('CHROME_PATH') or (str(mac) if mac.exists() else shutil.which('chromium'))
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(**({'executable_path':chrome} if chrome else {}),headless=True)
            for device,w,h in [('phone',390,884),('pad',768,1024)]:
                page=browser.new_page(viewport={'width':w,'height':h})
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(url+'/index.html')
                def record(scene,theme):
                    for row in page.evaluate(READ_BUTTONS):
                        row.update(device=device,scene=scene,theme=theme);rows.append(row)
                        if row['kind']=='structural': continue
                        reasons=[]
                        if row['kind']=='UNCLASSIFIED': reasons.append('button not classified')
                        if abs(row['height']-40)>.1: reasons.append('height')
                        if row['kind']=='icon' and abs(row['width']-40)>.1: reasons.append('icon width')
                        if row['font']!='14px' or row['line']!='20px': reasons.append('typography')
                        if row['clipped']: reasons.append('label clipped')
                        if reasons:failures.append({**row,'failures':reasons})
                    if scene in ['agents','plugins','skills','mcp']:
                        dims=page.locator('.z-directory-tools').evaluate('e=>({width:e.clientWidth,scroll:e.scrollWidth,heights:[...e.querySelectorAll("button,select")].map(x=>x.getBoundingClientRect().height)})')
                        if dims['scroll']>dims['width']+1 or any(abs(v-40)>.1 for v in dims['heights']):
                            failures.append({'device':device,'scene':scene,'theme':theme,'toolbar':dims})
                for theme in ['light','dark']:
                    page.evaluate('(t)=>dispatch("theme-"+t,null)',theme)
                    for scene in SCENES:
                        page.evaluate('(s)=>previewRoute(s)',scene)
                        if scene=='model-fetch':page.get_by_role('button',name='全选可添加项',exact=True).wait_for()
                        record(scene,theme)
                    for scene,action in [('model-detail','mc-model-add'),('agents','z-new'),('plugins','z-new'),('skills','z-new'),('mcp','z-new'),('memory','z-new'),('commands','z-new'),('hooks','z-new'),('tasks','create-task'),('tasks','permission')]:
                        page.evaluate('(s)=>previewRoute(s)',scene)
                        target=page.locator(f'[data-action="{action}"]').first
                        if not target.is_visible():raise AssertionError(f'missing modal trigger {scene}/{action}')
                        target.click();record(scene+'/'+action,theme)
                    page.evaluate('()=>previewRoute("plugins-import")')
                    page.get_by_label('来源链接',exact=True).fill('https://example.com/button-review.zip')
                    page.get_by_role('button',name='预览导入',exact=True).click()
                    record('plugins-import/preview',theme)
                page.close()
            # 同时核对外部评审工具栏。
            page=browser.new_page(viewport={'width':1280,'height':1400});page.goto(url+'/review.html?page=agents&theme=dark')
            controls=page.locator('button,select').evaluate_all('els=>els.map(e=>({height:e.getBoundingClientRect().height,font:getComputedStyle(e).fontSize}))')
            for item in controls:
                if abs(item['height']-40)>.1 or item['font']!='14px':failures.append({'review_control':item})
            page.screenshot(path=str(ROOT/'review/buttons-medium-dark.png'),full_page=True)
            page.get_by_label('统一主题',exact=True).select_option('light')
            page.screenshot(path=str(ROOT/'review/buttons-medium-light.png'),full_page=True)
            browser.close()
    finally:server.shutdown();server.server_close()
    result={'result':'passed' if not failures and not errors else 'failed','scenes':len(SCENES),'devices':['390x884','768x1024'],'themes':['light','dark'],'observations':len(rows),'medium_observations':sum(r['kind']=='medium' for r in rows),'icon_observations':sum(r['kind']=='icon' for r in rows),'structural_observations':sum(r['kind']=='structural' for r in rows),'failures':failures,'page_errors':errors}
    (ROOT/'review/button-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))
    if failures or errors:raise SystemExit(1)
if __name__=='__main__':main()
