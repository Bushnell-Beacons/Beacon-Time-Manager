"""Custom class lengths stay exact through editing, reload, calendar rendering, and PDFs."""
from pathlib import Path
from datetime import datetime,timezone
import subprocess
from playwright.sync_api import sync_playwright
HTML=Path('/workspace/artifacts/beacon-hosted-preview/index.html')
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1000},timezone_id='America/Los_Angeles',accept_downloads=True);page.clock.install(time=datetime(2026,11,9,20,tzinfo=timezone.utc));url='https://beacon-preview.invalid/';errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.route('**/*',lambda r:r.fulfill(content_type='text/html',body=HTML.read_text()) if r.request.url==url else r.abort());page.goto(url)
 page.locator('#add').click();page.locator('#evName').fill('Example Literature');page.locator('#evColor').fill('#865ab3');page.locator('#evStart').select_option('545');page.locator('[data-duration="50"]').click()
 assert page.locator('#evDuration').input_value()=='50' and page.locator('#evEnd').input_value()=='595';page.locator('#saveEvent').click()
 initial=page.evaluate("JSON.parse(localStorage.getItem('beacon-planner-v1')).events[0]");assert initial['end']-initial['start']==50 and initial['color']=='#865ab3'
 page.reload();page.locator('.event').filter(has_text='Example Literature').click();assert page.locator('#evDuration').input_value()=='50';page.locator('#evDuration').fill('37');assert page.locator('#evEnd').input_value()=='582';page.locator('#saveEvent').click()
 page.reload();page.locator('.event').filter(has_text='Example Literature').click();assert page.locator('#evEnd').input_value()=='582' and page.locator('#evDuration').input_value()=='37'
 page.locator('#evEnd').select_option('660');assert page.locator('#evDuration').input_value()=='115';page.locator('#evStart').select_option('600');assert page.locator('#evEnd').input_value()=='715'
 page.locator('#evDuration').fill('0');page.locator('#saveEvent').click();assert page.locator('#modal').is_visible() and page.locator('#err').inner_text();page.locator('#evDuration').fill('12.5');page.locator('#saveEvent').click();assert page.locator('#modal').is_visible();page.locator('#evDuration').fill('115');page.locator('#saveEvent').click()
 saved=page.evaluate("JSON.parse(localStorage.getItem('beacon-planner-v1')).events");assert len(saved)==1 and saved[0]['id']==initial['id'] and saved[0]['start']==600 and saved[0]['end']==715 and saved[0]['color']=='#865ab3'
 event=page.locator('.event').filter(has_text='Example Literature');assert event.count()==1 and event.bounding_box()['height']>page.locator('.slot').first.bounding_box()['height']
 page.locator('#add').click();page.locator('#evName').fill('Late study');page.locator('#evStart').select_option('1410');page.locator('#evDuration').fill('60');page.locator('#saveEvent').click();assert page.locator('#modal').is_visible();page.locator('#evDuration').fill('30');assert page.locator('#evEnd').input_value()=='1440';page.locator('#saveEvent').click()
 page.locator('#print').click();page.locator('input[name="pdfLayout"][value="agenda"]').check()
 with page.expect_download() as download:page.locator('#exportDownload').click()
 download.value.save_as('/tmp/beacon-class-durations.pdf');text=subprocess.check_output(['pdftotext','/tmp/beacon-class-durations.pdf','-']).decode();assert 'Example Literature' in text and '10:00 AM - 11:55 AM' in text;page.keyboard.press('Escape')
 for width in [390,768,1440]:
  page.set_viewport_size({'width':width,'height':1000});page.locator('#add').click();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.locator('#cancel').click()
 assert not errors,errors;b.close()
 print('PASS: preset/custom minute lengths, exact non-five-minute ends, start/end synchronization, editing without duplication, persistence/colors, invalid/overnight bounds, calendar blocks, PDF times and mobile widths')
