from playwright.sync_api import sync_playwright
import subprocess, re, tempfile, json, os

OUTPUT_FILE = 'schedule.json'
URL = 'https://opensauce.com/agenda/'

with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(ignore_https_errors=True)
    js_content = {'data': None}
    def handle_response(response):
        if 'schedule-overview-main' in response.url and response.url.endswith('.js'):
            try:
                js_content['data'] = response.text()
            except Exception:
                pass
    context.on('response', handle_response)
    page = context.new_page()
    page.goto(URL, timeout=60000)
    page.wait_for_load_state('networkidle')
    if not js_content['data']:
        raise RuntimeError('schedule script not found')
    data = js_content['data']

with tempfile.NamedTemporaryFile(delete=False, suffix='.js') as tmp:
    tmp.write(data.encode('utf-8'))
    tmp_path = tmp.name
node_script = (
    "const fs=require('fs');"
    f"const d=fs.readFileSync('{tmp_path}','utf8');"
    "const m=d.match(/var oo=(\\{.*?\\});/s);"
    "if(!m){throw new Error('not found');}"
    "const obj=eval('(' + m[1] + ')');"
    f"fs.writeFileSync('{OUTPUT_FILE}', JSON.stringify(obj, null, 2));"
)
subprocess.run(['node', '-e', node_script], check=True)
os.unlink(tmp_path)
print('Saved', OUTPUT_FILE)
