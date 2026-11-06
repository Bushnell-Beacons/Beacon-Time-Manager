"""Regression: one continuous block per competition, with estimated end and new layout."""
from datetime import datetime,timezone
from pathlib import Path
import os,json
from playwright.sync_api import sync_playwright
from browser_test_helpers import wait_js
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1440,'height':1000},timezone_id='America/Los_Angeles')
 page.clock.install(time=datetime(2026,10,29,20,tzinfo=timezone.utc))
 game={'id':'one','title':'Continuous Test Game','start':'2026-10-29T12:30:00-07:00','allDay':False}
 data={'events':[game,game,{**game,'id':'two','start':'2026-10-29T17:00:00-07:00'}],'fetchedAt':'2026-10-29T12:00:00Z'}
 page.route('**/schedules/baseball.json',lambda route:route.fulfill(json=data))
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(os.environ.get('BEACON_TEST_URL','http://127.0.0.1:8002'))
 page.locator('#sport').select_option('baseball')
 wait_js(page,"document.querySelectorAll('.official-event').length===2")
 assert page.locator('.official-event').count()==2
 first=page.locator('.official-event').first
 assert '(est.)' in first.inner_text()
 assert first.bounding_box()['height']>page.locator('.slot').first.bounding_box()['height']*2
 assert page.locator('.slot[data-day="4"][data-hour="13"] .official-event').count()==0
 assert page.locator('.priorities-row #goals').count()==1
 assert page.locator('.priorities-row #reminders').count()==1
 assert page.locator('.sidebar #goals,.sidebar #reminders').count()==0
 assert page.locator('.sport-question').inner_text()=='What’s your sport?'
 snapshot=page.evaluate('window.BeaconPlanner.getSchedule()')
 games=[e for d in snapshot['days'] for e in d['events'] if e['title']=='Continuous Test Game']
 assert len(games)==2 and all(e['estimated'] and e['end']-e['start']>60 for e in games)
 page.locator('.official-event').first.click()
 assert page.locator('#gameDetails').is_visible()
 page.locator('#closeGameDetails').click()
 # Dialog handled automatically by Playwright when no listeners exist.
 page.locator('#print').click()
 page.locator('input[name="pdfLayout"][value="agenda"]').check()
 with page.expect_download() as download:page.locator('#exportDownload').click()
 download.value.save_as('/tmp/beacon-estimated-games.pdf')
 import subprocess
 text=subprocess.check_output(['pdftotext','/tmp/beacon-estimated-games.pdf','-']).decode()
 assert '(est.)' in text and text.count('Continuous Test Game')==2,text
 page.keyboard.press('Escape')
 for width in [390,768,1440]:
  page.set_viewport_size({'width':width,'height':1000})
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
 page.set_viewport_size({'width':1440,'height':1000})
 page.screenshot(path='/tmp/beacon-continuous-games.png',full_page=True)
 assert not errors,errors
 browser.close()
 print('PASS: one continuous block per game, distinct second game retained, estimated finishes, priorities at top, compact sport selector, responsive layout')
