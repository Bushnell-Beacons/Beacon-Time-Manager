"""Synthetic games stay in the in-memory test bundle, never published schedule data."""
from pathlib import Path
from datetime import datetime,timezone
from base64 import b64encode
from hashlib import sha256
import re,json,sys
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).parent))
from browser_test_helpers import wait_js
html=Path('/workspace/artifacts/beacon-hosted-preview/index.html').read_text()
bootstrap=next(m for m in re.finditer(r'<script>(.*?)</script>',html,re.S) if 'const saved=' in m[1]);old=bootstrap[1];match=re.search(r'const saved=(.*?);\n  window.BEACON_REVIEW_PRIVATE=',old,re.S);saved=json.loads(match[1])
def game(uid,title,start,**extra):return {'id':uid,'title':title,'start':start,'end':None,'allDay':False,'status':'',**extra}
saved['sports']['mens-soccer']={'events':[
 game('completed','Example Completed Opponent','2026-11-05T15:30:00-08:00'),
 game('still-playing','Example Unfinished Opponent','2026-11-06T12:00:00-08:00'),
 game('old','Example Old Game','2026-11-01T12:00:00-08:00'),
 game('cancelled','Example Cancelled Game','2026-11-06T08:00:00-08:00',status='CANCELLED'),
 game('postponed','Example Postponed Game','2026-11-06T09:00:00-08:00',status='POSTPONED'),
 game('unknown','Example TBA Game','2026-11-06',allDay=True,timeUnknown=True),
]}
saved['sports']['womens-soccer']={'events':[game('women-completed','Example Other Opponent','2026-11-05T16:00:00-08:00')]}
saved['sports']['baseball']={'events':[game('future','Example Future Opponent','2026-11-07T11:00:00-08:00')]}
payload=json.dumps(saved,ensure_ascii=True).replace('<','\\u003c');new=old[:match.start(1)]+payload+old[match.end(1):];fixture=html[:bootstrap.start(1)]+new+html[bootstrap.end(1):];fixture=fixture.replace("'sha256-"+b64encode(sha256(old.encode()).digest()).decode()+"'","'sha256-"+b64encode(sha256(new.encode()).digest()).decode()+"'")
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);context=b.new_context(viewport={'width':1440,'height':1000},timezone_id='America/Los_Angeles');page=context.new_page();page.clock.install(time=datetime(2026,11,6,20,tzinfo=timezone.utc))
 requests=[];errors=[];page.on('request',lambda r:requests.append(r.url));page.on('pageerror',lambda e:errors.append(str(e)));url='https://beacon-preview.invalid/'
 context.route('**/*',lambda r:r.fulfill(content_type='text/html',body=fixture) if r.request.url==url else r.abort());page.goto(url)
 goal='Finish assignment <img src=x onerror=alert(1)>'
 page.locator('#goalInput').fill(goal);page.locator('#addGoal').click();page.locator('#goals input').check();assert page.locator('#goalCelebration').is_visible();assert page.locator('#goalCelebration p').inner_text()==goal;assert page.locator('#goalCelebration img').count()==0
 page.clock.run_for(5500);assert not page.locator('#goalCelebration').is_visible();page.locator('#goals input').uncheck();assert not page.locator('#goalCelebration').is_visible();page.locator('#goals input').check();assert page.locator('#goalCelebration').is_visible()
 page.reload();assert not page.locator('#goalCelebration').is_visible();assert page.locator('#goals input').is_checked()
 page.locator('#sport').select_option('baseball');wait_js(page,"document.getElementById('sportStatus').textContent.includes('official competitions loaded')");assert not page.locator('#gameCheckin').is_visible()
 page.locator('#sport').select_option('mens-soccer');assert page.locator('#gameCheckin').is_visible();assert 'Example Completed Opponent' in page.locator('#gameCheckinDetail').inner_text()
 page.locator('[data-outcome="win"]').click();assert page.locator('#gameCheckinTitle').inner_text()=='Beacons win!';assert page.locator('.celebration-confetti i').count()>0
 records=page.evaluate("JSON.parse(localStorage.getItem('beacon-planner-v1')).gameCheckins");assert records['mens-soccer|official|completed']['outcome']=='win'
 page.locator('.game-change').click();page.locator('[data-outcome="loss"]').click();assert 'One game doesn’t define' in page.locator('.game-feedback').inner_text();assert page.locator('.celebration-confetti i').count()==0;page.locator('.game-done').click()
 page.reload();wait_js(page,"document.getElementById('sportStatus').textContent.includes('official competitions loaded')");assert not page.locator('#gameCheckin').is_visible()
 page.locator('#sport').select_option('womens-soccer');assert page.locator('#gameCheckin').is_visible();page.locator('.game-later').click();page.reload();wait_js(page,"document.getElementById('sportStatus').textContent.includes('official competitions loaded')");assert not page.locator('#gameCheckin').is_visible()
 page.clock.run_for(61*60*1000);assert page.locator('#gameCheckin').is_visible();page.keyboard.press('Escape');assert not page.locator('#gameCheckin').is_visible();page.clock.run_for(61*60*1000);assert page.locator('#gameCheckin').is_visible();page.locator('.game-skip').click();page.reload();wait_js(page,"document.getElementById('sportStatus').textContent.includes('official competitions loaded')");assert not page.locator('#gameCheckin').is_visible()
 page.emulate_media(reduced_motion='reduce');page.locator('#goals input').uncheck();page.locator('#goals input').check();assert page.locator('#goalCelebration').is_visible();assert page.locator('.celebration-confetti i').count()==0;page.locator('#goalCelebration button').click()
 page.on('dialog',lambda d:d.accept());page.locator('details.privacy-panel').evaluate('(e)=>e.open=true');page.locator('#privateSession').check();assert page.evaluate("localStorage.getItem('beacon-planner-v1')") is None
 page.reload();page.locator('#sport').select_option('womens-soccer');assert page.locator('#gameCheckin').is_visible();page.locator('[data-outcome="tie"]').click();assert 'Take what you learned' in page.locator('.game-feedback').inner_text();assert page.evaluate("localStorage.getItem('beacon-planner-v1')") is None
 for width in [390,768,1440]:
  page.set_viewport_size({'width':width,'height':1000});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 assert not errors,errors;assert all(r==url for r in requests),requests
 print('PASS: goal celebrations; safe text; completed games only; win/loss/tie feedback; saved answers; change answer; snooze/Escape/skip; reduced motion; private sessions; mobile layouts; no uploads')
 b.close()
