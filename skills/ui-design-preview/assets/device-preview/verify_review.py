"""检验评审器的可观察联动行为；需已有 Playwright 与 Chrome，不自动安装。"""
from pathlib import Path
import argparse
import json
import os
import shutil
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parent

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', help='可选现有评审页URL；缺省临时启动当前目录')
    parser.add_argument('--screenshot', help='可选评审截图输出路径')
    args = parser.parse_args()
    server = None
    if not args.url:
        server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
        threading.Thread(target=server.serve_forever, daemon=True).start()
    url = args.url or f'http://127.0.0.1:{server.server_port}/review.html?section=models'
    mac = Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    chrome = os.environ.get('CHROME_PATH') or (str(mac) if mac.exists() else None) or shutil.which('google-chrome') or shutil.which('chromium')
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(**({'executable_path': chrome} if chrome else {}), headless=True)
            page = browser.new_page(viewport={'width':1280,'height':1400})
            errors, missing = [], []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('response', lambda r: missing.append(r.url) if r.status >= 400 else None)
            page.goto(url)
            phone, pad = page.frame_locator('#phone'), page.frame_locator('#pad')
            control = page.get_by_label('统一页面', exact=True)
            expect(control).to_be_visible()
            control.select_option('skills-import')
            for frame in [phone,pad]:expect(frame.get_by_role('dialog',name='导入技能')).to_be_visible()
            page.get_by_label('Phone 页面',exact=True).select_option('model-detail')
            for frame in [phone,pad]:expect(frame.locator('.mw-detail')).to_be_visible()
            expect(page.get_by_label('Pad 页面',exact=True)).to_have_value('model-detail')
            page.get_by_label('统一主题',exact=True).select_option('dark')
            for frame in [phone,pad]:expect(frame.locator('body')).not_to_have_class('theme-light')
            page.get_by_label('同步两端',exact=True).uncheck()
            page.get_by_label('Phone 页面',exact=True).select_option('skills-import')
            expect(phone.get_by_role('dialog',name='导入技能')).to_be_visible()
            expect(pad.locator('.mw-detail')).to_be_visible()
            page.get_by_label('Phone 主题',exact=True).select_option('light')
            expect(phone.locator('body')).to_have_class('theme-light')
            expect(pad.locator('body')).not_to_have_class('theme-light')
            # 界面内部操作也应联动，而不仅仅是评审器选择框。
            page.get_by_label('同步两端',exact=True).check()
            control.select_option('plugins-import')
            pad.get_by_role('tab',name='压缩文件',exact=True).click()
            expect(phone.get_by_role('tab',name='压缩文件',exact=True)).to_have_attribute('aria-selected','true')
            phone.get_by_role('tab',name='链接地址',exact=True).click()
            expect(pad.get_by_role('tab',name='链接地址',exact=True)).to_have_attribute('aria-selected','true')
            phone.get_by_label('来源链接',exact=True).fill('https://example.com/private-draft.zip')
            expect(pad.get_by_label('来源链接',exact=True)).to_have_value('')
            phone.get_by_role('button',name='关闭导入',exact=True).click()
            expect(pad.get_by_role('dialog',name='导入插件')).not_to_be_visible()
            pad.locator('[data-action="z-category"][data-id="model"]').click()
            expect(page.get_by_label('Phone 页面',exact=True)).to_have_value('model')
            phone.locator('[data-action="mc-edit"][data-id="fixture-personal"]').click()
            expect(pad.get_by_label('连接名称',exact=True)).to_have_value('个人 OpenAI')
            phone.get_by_role('button',name='获取模型',exact=True).click()
            expect(pad.get_by_role('dialog',name='获取模型',exact=True)).to_be_visible()
            pad.get_by_role('button',name='关闭模型面板',exact=True).click()
            expect(phone.get_by_role('dialog',name='获取模型',exact=True)).not_to_be_visible()
            phone.get_by_role('button',name='添加模型',exact=True).click()
            expect(pad.get_by_role('dialog',name='添加模型',exact=True)).to_be_visible()
            phone.locator('#manual-model-id').fill('only-on-phone')
            phone.get_by_role('button',name='确认',exact=True).click()
            expect(pad.locator('#manual-model-id')).to_have_value('')
            expect(pad.locator('.mw-model-table')).not_to_contain_text('only-on-phone')
            control.select_option('appearance')
            phone.locator('[data-action="theme-dark"]').click()
            expect(pad.locator('body')).not_to_have_class('theme-light')
            page.get_by_label('同步两端',exact=True).uncheck()
            control.select_option('plugins-import')
            pad.get_by_role('tab',name='压缩文件',exact=True).click()
            expect(phone.get_by_role('tab',name='链接地址',exact=True)).to_have_attribute('aria-selected','true')
            page.get_by_label('同步两端',exact=True).check()
            expect(phone.get_by_role('tab',name='压缩文件',exact=True)).to_have_attribute('aria-selected','true')
            # 还原原有独立URL用例。
            control.select_option('model-detail')
            page.get_by_label('统一主题',exact=True).select_option('dark')
            page.get_by_label('同步两端',exact=True).uncheck()
            page.get_by_label('Phone 页面',exact=True).select_option('skills-import')
            page.get_by_label('Phone 主题',exact=True).select_option('light')
            saved_url=page.url
            page.reload()
            expect(page.get_by_label('同步两端',exact=True)).not_to_be_checked()
            expect(phone.get_by_role('dialog',name='导入技能')).to_be_visible()
            expect(pad.locator('.mw-detail')).to_be_visible()
            assert page.url == saved_url
            # 再选择一次明确最近操作端，然后联动。
            page.get_by_label('Phone 页面',exact=True).select_option('agents-import')
            page.get_by_label('同步两端',exact=True).check()
            for frame in [phone,pad]:expect(frame.get_by_role('dialog',name='导入子智能体')).to_be_visible()
            for frame in [phone,pad]:expect(frame.locator('body')).to_have_class('theme-light')
            page.get_by_role('button',name='下一页',exact=True).click()
            expect(control).to_have_value('plugins-import')
            page.get_by_role('button',name='上一页',exact=True).click()
            expect(control).to_have_value('agents-import')
            # 遍历实际注册场景，确认两个文档均落到目标页且无脚本/资源错误。
            values=control.locator('option').evaluate_all('(nodes)=>nodes.map(n=>n.value)')
            for value in values:
                control.select_option(value)
                expect(page.get_by_label('Phone 页面',exact=True)).to_have_value(value)
                expect(page.get_by_label('Pad 页面',exact=True)).to_have_value(value)
                expect(page.locator('#review-status')).not_to_contain_text('失败')
            control.select_option('model-detail')
            # 帧重载时，后续选择应保留并应用到新文档。
            page.eval_on_selector('#phone', '(f)=>f.contentWindow.location.reload()')
            control.select_option('plugins-import')
            expect(phone.get_by_role('dialog',name='导入插件')).to_be_visible()
            expect(pad.get_by_role('dialog',name='导入插件')).to_be_visible()
            # 暂无适配器时必须显式报错；重载恢复。
            page.frame(name='phone').evaluate('window.previewRoute=undefined')
            control.select_option('skills')
            expect(page.locator('#review-status')).to_contain_text('失败')
            page.eval_on_selector('#phone', '(f)=>f.contentWindow.location.reload()')
            expect(page.locator('#review-status')).not_to_contain_text('失败')
            control.select_option('model-detail')
            for frame in [phone,pad]:expect(frame.locator('.mw-detail')).to_be_visible()
            assert page.frame(name='phone').evaluate('innerWidth') == 390
            assert page.frame(name='pad').evaluate('innerWidth') == 768
            page.set_viewport_size({'width':800,'height':1200})
            assert page.frame(name='phone').evaluate('innerWidth') == 390
            assert page.frame(name='pad').evaluate('innerWidth') == 768
            assert page.evaluate('document.body.scrollWidth<=innerWidth')
            # 确定性延迟Pad入口，不靠等待毫秒数猜测加载竞态。
            held=[]
            def hold_pad(route):
                if route.request.frame.name == 'pad':held.append(route)
                else:route.continue_()
            page.route('**/index.html*', hold_pad)
            page.goto(url.split('?')[0]+'?page=chat&theme=light',wait_until='domcontentloaded')
            control.select_option('model-detail')
            expect(phone.locator('.mw-detail')).to_be_visible()
            control.select_option('skills-import')
            control.select_option('plugins-import')
            expect(phone.get_by_role('dialog',name='导入插件')).to_be_visible()
            expect(page.locator('#review-status')).to_contain_text('正在加载 Pad')
            assert held,'Pad request was not intercepted'
            for request in held:request.continue_()
            page.unroute('**/index.html*',hold_pad)
            expect(pad.get_by_role('dialog',name='导入插件')).to_be_visible()
            expect(page.locator('#review-status')).to_contain_text('联动已开启')
            page.goto(url.split('?')[0]+'?page=unknown&theme=unknown')
            expect(control).to_have_value('chat')
            expect(page.get_by_label('统一主题',exact=True)).to_have_value('light')
            control.select_option('model-detail')
            for frame in [phone,pad]:expect(frame.locator('.mw-detail')).to_be_visible()
            page.set_viewport_size({'width':1280,'height':1400})
            # 等布局与合成帧稳定再取证，避免ResizeObserver缩放过程中的截图。
            page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
            if args.screenshot:
                control.select_option('plugins-import')
                pad.get_by_role('tab',name='压缩文件',exact=True).click()
                expect(phone.get_by_role('tab',name='压缩文件',exact=True)).to_have_attribute('aria-selected','true')
                page.screenshot(path=args.screenshot,full_page=True)
            assert not errors,errors
            assert not missing,missing
            browser.close()
            print(json.dumps({'result':'passed','scenes':len(values),'checks':['internal-navigation-dialog-tabs','no-input-or-save-broadcast','global-and-panel-sync','theme-sync','independent-mode','rejoin-latest-device','url-restore','previous-next','all-routes','frame-reload','delayed-frame-latest-selection','invalid-url-fallback','adapter-error','fixed-viewports','no-resource-errors'],'page_errors':errors,'missing_resources':missing},ensure_ascii=False))
    finally:
        if server:server.shutdown();server.server_close()

if __name__=='__main__':main()
