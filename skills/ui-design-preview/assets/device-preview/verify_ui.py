"""可点击原型验收；验证界面行为，不验证模型或系统能力。"""
from pathlib import Path
import json
import os
import io
import zipfile
import shutil
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass
server=None
BASE=os.environ.get('DEMO_URL')
if not BASE:
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    BASE=f'http://127.0.0.1:{server.server_port}/index.html'
mac=Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
chrome=os.environ.get('CHROME_PATH') or (str(mac) if mac.exists() else None) or shutil.which('google-chrome') or shutil.which('chromium')
OUT=Path(__file__).parent/'review'
OUT.mkdir(exist_ok=True)
reports=[]
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(**({'executable_path':chrome} if chrome else {}),headless=True)
        for device,w,h in [('phone',390,884),('pad',768,1024)]:
            page=browser.new_page(viewport={'width':w,'height':h},device_scale_factor=1)
            page.set_default_timeout(4000)
            errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            def click(action):
                nodes=page.locator(f'[data-action="{action}"]:visible')
                for i in range(nodes.count()):
                    box=nodes.nth(i).bounding_box()
                    if box and box['x']>=0 and box['x']<w:
                        nodes.nth(i).click()
                        return
                raise AssertionError('No reachable control: '+action)
            def shot(name):
                assert page.evaluate('document.body.scrollWidth <= innerWidth'),name+' body overflow'
                assert page.evaluate('[...document.querySelectorAll(".page-scroll,.z-main")].every(e=>e.scrollWidth<=e.clientWidth+1)'),name+' content overflow'
                page.screenshot(path=str(OUT/f'{device}-{name}.png'))
            page.goto(BASE)
            shot('home')
            click('model');page.locator('[data-model="推理模型"]').click()
            assert page.locator('.composer-mini').inner_text().strip().startswith('推理模型')
            shot('home')
            if device!='desktop':
                page.locator('.menu-button').click()
                shot('drawer')
                page.keyboard.press('Escape')
                assert not page.locator('.scrim').is_visible()
            click('go-discover')
            shot('discover')
            click('category-skill')
            if device=='pad':click('pad-open')
            else:page.locator('[data-id="deep-research"]').click()
            click('add-item');click('confirm-add')
            assert page.locator('[data-action="remove-item"]').count()==1
            shot('capability-detail')
            click('go-tasks')
            click('create-task')
            page.locator('#schedule-name').fill('每日研究简报')
            page.locator('#schedule-time').fill('08:30')
            click('confirm-schedule')
            assert page.get_by_role('heading',name='每日研究简报').count()==1
            shot('tasks')
            click('go-me');click('go-settings')
            shot('settings')
            if device=='phone':page.locator('[data-id="general"]').click()
            shot('general')
            if device!='desktop':
                assert page.locator('[data-id="browser"]').count()==0
                assert page.locator('[data-id="computer"]').count()==0
                assert page.locator('[data-id="shortcuts"]').count()==0
            def category(name):
                if page.locator('[data-action="mc-exit"]').count():click('mc-exit')
                elif device=='phone':
                    click('z-back')
                    if page.locator('.mw-providers').count():click('z-back')
                page.locator(f'[data-id="{name}"]').click()
            category('appearance');shot('appearance');click('theme-light');shot('appearance-light')
            category('general');shot('general-light')
            category('agents');shot('agents');click('z-new')
            page.locator('[name="名称"]').fill('资料核对员')
            page.locator('[name="内容"]').fill('核对每一条来源，输出可追溯摘要。')
            click('z-editor-save')
            assert page.get_by_role('button',name='资料核对员',exact=False).count()>0
            page.locator('[data-config-name="资料核对员"] .z-config-main').click()
            assert page.locator('[name="内容"]').input_value()=='核对每一条来源，输出可追溯摘要。'
            click('z-editor-close')
            category('model');shot('models')
            if device=='phone':page.locator('[data-id="fixture-team"]').click()
            shot('model-editor')
            click('mc-fetch');page.wait_for_timeout(500);shot('model-fetch')
            assert page.locator('[data-fetch-id="demo-chat"]').is_disabled()
            page.locator('#fetch-scenario').select_option('empty')
            assert page.get_by_text('没有返回模型',exact=False).is_visible()
            shot('model-fetch-empty')
            page.locator('#fetch-scenario').select_option('error');shot('model-fetch-error')
            click('mc-fetch-retry');page.wait_for_timeout(500)
            page.locator('#model-search').fill('no-such-model')
            assert page.get_by_text('没有匹配的模型 ID').is_visible()
            page.locator('#model-search').fill('')
            click('mc-fetch-all');click('mc-fetch-confirm')
            assert page.locator('.mc-model-line').count()==5
            click('mc-save')
            if device=='phone':click('z-back')
            click('mc-add');shot('model-providers')
            page.locator('#provider-search').fill('百炼')
            assert page.locator('.provider-directory .provider-choice').count()==1
            assert page.locator('.provider-directory').get_by_text('阿里云百炼',exact=True).count()==1
            page.locator('#provider-search').fill('不存在的厂商')
            assert page.get_by_text('没有找到该服务商，可使用下方自定义连接。').is_visible()
            page.locator('#provider-search').fill('')
            page.locator('[data-provider="openai"]:visible').last.click()
            page.locator('[name="名称"]').fill('测试连接')
            page.locator('[name="APIKey"]').fill('demo-key-not-a-real-secret')
            click('mc-model-add')
            page.locator('[name="模型ID"]').fill('example-model')
            click('mc-manual-confirm')
            click('mc-model-add')
            page.locator('[name="模型ID"]').fill('example-model')
            click('mc-manual-confirm')
            assert page.get_by_text('此模型已添加，请使用其他 ID。').is_visible()
            click('mc-dialog-close')
            assert page.locator('[name="名称"]').input_value()=='测试连接'
            assert page.locator('[name="APIKey"]').input_value()=='demo-key-not-a-real-secret'
            page.locator('[name="BaseURL"]').fill('https://example.com/v1')
            assert page.locator('[name="APIKey"]').input_value()==''
            page.locator('[name="APIKey"]').fill('demo-key-not-a-real-secret')
            click('mc-test')
            assert page.locator('[name="APIKey"]').input_value()==''
            assert 'demo-key-not-a-real-secret' not in page.evaluate('JSON.stringify(localStorage)')
            click('mc-save')
            page.locator('[name="名称"]').fill('未保存的名称')
            if device=='phone':click('z-back')
            else:page.locator('.mw-provider').filter(has_text='团队模型网关').click()
            assert page.get_by_role('dialog',name='保存当前配置？').is_visible()
            click('mc-dialog-close')
            assert page.locator('[name="名称"]').input_value()=='未保存的名称'
            if device=='phone':click('z-back')
            else:page.locator('.mw-provider').filter(has_text='团队模型网关').click()
            click('mc-discard')
            page.locator('.mw-provider').filter(has_text='测试连接').click()
            assert page.locator('[name="BaseURL"]').input_value()=='https://example.com/v1'
            assert page.locator('.mc-model-line').get_by_text('example-model',exact=True).is_visible()
            for name in ['memory','plugins','mcp','skills','commands','hooks','usage']:
                category(name)
                assert page.locator('.z-content').is_visible()
                assert page.evaluate('document.body.scrollWidth <= innerWidth')
            for kind in ['skills','agents','plugins']:
                category(kind)
                click('z-import')
                page.locator('#import-url').fill('not-a-link')
                click('imp-preview')
                assert page.locator('#import-error').inner_text()
                page.locator('#import-url').fill('https://example.com/resources/'+kind+'.zip')
                shot(kind+'-import')
                click('imp-preview');shot(kind+'-import-preview')
                click('imp-confirm')
                row=page.locator('[data-config-name="'+kind+'"]')
                assert row.is_visible()
                assert row.get_by_role('switch',include_hidden=True).is_disabled()
                click('z-import')
                page.locator('[data-mode="archive"]').click()
                page.locator('#import-file').set_input_files({'name':'bad.txt','mimeType':'text/plain','buffer':b'bad'})
                assert page.get_by_text('暂不支持此格式，请选择 ZIP 文件。').is_visible()
                page.locator('#import-file').set_input_files({'name':'empty.zip','mimeType':'application/zip','buffer':b''})
                assert page.get_by_text('文件为空，请重新选择。').is_visible()
                buf=io.BytesIO()
                with zipfile.ZipFile(buf,'w') as z:z.writestr('README.md','local fixture')
                page.locator('#import-file').set_input_files({'name':kind+'.zip','mimeType':'application/zip','buffer':buf.getvalue()})
                shot(kind+'-import-archive')
                click('imp-preview');click('imp-confirm')
                assert page.get_by_text('已存在同名项目，请修改名称；不会覆盖已有内容。').is_visible()
                page.locator('#import-name').fill(kind+'-zip')
                click('imp-confirm')
                assert page.locator('[data-config-name="'+kind+'-zip"]').is_visible()
                click('z-import');click('imp-close')
                assert page.locator('.import-dialog').count()==0
            category('appearance');click('theme-dark')
            if device=='phone':click('z-back')
            click('go-chat')
            page.locator('#task-draft').fill('请整理这些资料')
            click('send')
            assert page.get_by_text('请整理这些资料',exact=True).count()==1
            shot('conversation')
            assert not errors,errors
            reports.append({'device':device,'viewport':f'{w}x{h}','result':'passed','page_errors':errors,'checks':['drawer','catalog-add','schedule-form','settings-navigation','device-boundary','theme','agent-draft-roundtrip','model-selection','provider-search-and-empty','connection-draft-roundtrip','model-fetch-selection-dedup','model-fetch-empty-error-retry','manual-model-duplicate','three-kind-link-zip-import','import-invalid-empty-collision-cancel','credential-target-clear','no-key-storage','conversation']})
            page.close()
        browser.close()
    (OUT/'verification.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(reports,ensure_ascii=False,indent=2))
finally:
    if server:server.shutdown();server.server_close()
