"""Hidden games stay local and removed across schedule reloads, with restore and private mode."""
from pathlib import Path
from datetime import datetime,timezone
from base64 import b64encode
from hashlib import sha256
import re,json,sys,subprocess
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).parent))
from browser_test_helpers import wait_js
html=Path('/workspace/artifacts/beacon-hosted-preview/index.html').read_text();bootstrap=next(m for m in re.finditer(r'<script>(.*?)</script>',html,re.S) if 'const saved=' in m[1]);old=bootstrap[1];match=re.search(r'const saved=(.*?);\n  window.BEACON_REVIEW_PRIVATE=',old,re.S);payload=json.loads(match[1]);payload['sports']['mens-soccer']={'events':[
 {'id':'hide','title':'Example game to remove','start':'2026-11-07T16:00:00-08:00','end':None,'allDay':False},
 {'id':'keep','title':'Example game to keep','start':'2026-11-07T12:00:00-08:00','end':None,'allDay':False},
 {'id':'tba','title':'Example TBA game','start':'2026-11-08','end':None,'allDay':True,'timeUnknown':True,'timeLabel':'Time TBA'},
]}
new=old[:match.start(1)]+json.dumps(payload,ensure_ascii=True).replace('<','\\u003c')+old[match.end(1):];fixture=html[:bootstrap.start(1)]+new+html[bootstrap.end(1):];fixture=fixture.replace("'sha256-"+b64encode(sha256(old.encode()).digest()).decode()+"'","'sha256-"+b64encode(sha256(new.encode()).digest()).decode()+"'")
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1000},timezone_id='America/Los_Angeles',accept_downloads=True);page.clock.install(time=datetime(2026,11,6,20,tzinfo=timezone.utc));url='https://beacon-preview.invalid/';requests=[];page.on('request',lambda r:requests.append(r.url));errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.route('**/*',lambda r:r.fulfill(content_type='text/html',body=fixture) if r.request.url==url else r.abort());page.goto(url)
 page.locator('#sport').select_option('mens-soccer');wait_js(page,"document.getElementById('sportStatus').textContent.includes('official competitions loaded')")
 target=page.locator('.official-event').filter(has_text='Example game to remove');assert target.count()==1;target.click();assert page.locator('#gameDetails').is_visible();page.locator('#removeGame').click();assert target.count()==0
 assert page.locator('.official-event').filter(has_text='Example game to keep').count()==1
 assert page.evaluate("BeaconPlanner.getSchedule().days.every(d=>d.events.every(e=>e.title!=='Example game to remove'))")
 assert page.evaluate("JSON.parse(localStorage.getItem('beacon-planner-v1')).hiddenGames") == ['mens-soccer|official|hide']
 page.reload();wait_js(page,"document.getElementById('sportStatus').textContent.includes('official competitions loaded')");assert target.count()==0
 page.locator('#print').click();page.locator('input[name="pdfLayout"][value="agenda"]').check()
 with page.expect_download() as download:page.locator('#exportDownload').click()
 download.value.save_as('/tmp/beacon-removed-games.pdf');text=subprocess.check_output(['pdftotext','/tmp/beacon-removed-games.pdf','-']).decode();assert 'Example game to remove' not in text and 'Example game to keep' in text;page.keyboard.press('Escape')
 page.locator('#removedGames').evaluate('(e)=>e.open=true');page.get_by_role('button',name='Restore Example game to remove',exact=True).click();assert target.count()==1
 target.click();page.locator('#removeGame').click();page.locator('details.sport-options').evaluate('(e)=>e.open=true');page.locator('#syncSport').click();wait_js(page,"document.getElementById('sportStatus').textContent.includes('official competitions loaded')");assert target.count()==0
 page.locator('#nextWeek').click();page.locator('.calendar-note-game').filter(has_text='Example TBA game').click();page.locator('#removeGame').click();assert 'Example TBA game' not in page.locator('#calendarNotes').inner_text()
 page.clock.fast_forward(48*60*60*1000);assert page.evaluate("BeaconPlanner.getGameCheckinState().games.every(e=>!e.id.endsWith('|hide'))")
 # Dismiss any check-in for the remaining visible game.
 if page.locator('#gameCheckin').is_visible():page.locator('.game-skip').click()
 page.on('dialog',lambda d:d.accept());page.locator('details.privacy-panel').evaluate('(e)=>e.open=true');page.locator('#privateSession').check();assert page.evaluate("localStorage.getItem('beacon-planner-v1')") is None
 for width in [390,768,1440]:
  page.set_viewport_size({'width':width,'height':1000});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
 assert not errors,errors;assert all(r==url for r in requests),requests
 print('PASS: remove timed/TBA games locally; persist across reload and schedule refresh; exclude from agenda/PDF/check-ins; restore; private storage; responsive layouts; no uploads')
 b.close()
