(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const planner = window.BeaconPlanner;
  const showAcademic=$('showAcademic');
  function syncAcademicChoice(){showAcademic.checked=planner.getAcademicVisibility();}
  showAcademic.onchange=()=>planner.setAcademicVisibility(showAcademic.checked);
  document.addEventListener('beacon:render',syncAcademicChoice);syncAcademicChoice();
  $('goals').closest('section').classList.add('goals-card');
  $('reminders').closest('section').classList.add('reminders-card');
  const priorities=document.createElement('div');priorities.className='priorities-row';priorities.setAttribute('aria-label','Goals and reminders');
  document.querySelector('.layout').before(priorities);
  priorities.append($('goals').closest('section'),$('reminders').closest('section'));
  const agenda = document.createElement('div');
  agenda.id = 'agendaView'; agenda.className = 'agenda-view';
  agenda.innerHTML = '<nav id="agendaDays" class="agenda-days" aria-label="Choose an agenda day"></nav><div class="agenda-heading"><div><span class="section-index">DAILY SCHEDULE</span><h3 id="agendaDate"></h3></div><button id="agendaAdd" type="button">+ Add activity</button></div><div id="agendaEvents" class="agenda-events"></div>';
  document.querySelector('.calendar-wrap').before(agenda);
  const dashboardAgenda = $('dashboardAgendaCard');
  let selectedDay = new Date().getDay();
  function formatTime(minutes) {
    const m = minutes % 1440, h = Math.floor(m / 60);
    return `${h % 12 || 12}:${String(m % 60).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}`;
  }
  function renderAgenda() {
    const schedule = planner.getSchedule();
    $('agendaDays').replaceChildren();
    schedule.days.forEach(day => {
      const button = document.createElement('button'); button.type = 'button'; button.setAttribute('aria-pressed', String(day.index === selectedDay));
      const label = document.createElement('strong'); label.textContent = day.shortLabel;
      const count = document.createElement('span'); count.textContent = day.events.length + (day.events.length === 1 ? ' activity' : ' activities');
      button.append(label, count); button.onclick = () => {selectedDay = day.index; renderAgenda();}; $('agendaDays').append(button);
    });
    const day = schedule.days[selectedDay]; $('agendaDate').textContent = day.label;
    $('agendaEvents').replaceChildren();
    if (!day.events.length) {
      const empty = document.createElement('div'); empty.className = 'agenda-empty';
      const title = document.createElement('h4'); title.textContent = 'No activities scheduled';
      const detail = document.createElement('p'); detail.textContent = 'Add a class or personal activity for this day.';
      empty.append(title, detail); $('agendaEvents').append(empty);
    }
    const academicDetails=document.createElement('details');academicDetails.className='agenda-academic-dates';
    const academicSummary=document.createElement('summary');academicSummary.textContent='University dates ('+day.events.filter(e=>e.academic).length+')';academicDetails.append(academicSummary);
    day.events.forEach(event => {
      const button = document.createElement('button'); button.type = 'button'; button.className = 'agenda-event'; button.style.setProperty('--event-color', event.color);
      const time = document.createElement('span'); time.className = 'agenda-event-time'; time.textContent = event.allDay ? (event.timeUnknown ? event.timeLabel || 'Time TBA' : 'All day') : formatTime(event.start);
      if (!event.allDay && event.endKnown) {const end = document.createElement('small'); end.textContent = 'to ' + formatTime(event.end) + (event.estimated ? ' (est.)' : ''); time.append(end);}
      const body = document.createElement('span'); body.className = 'agenda-event-body';
      const title = document.createElement('strong'); title.textContent = event.title;
      const detail = document.createElement('small'); detail.textContent = [event.category, event.location, event.attendance, event.description].filter(Boolean).join(' · ');
      body.append(title, detail);
      const action = document.createElement('span'); action.className = 'agenda-event-action'; action.textContent = event.personal ? 'Edit activity' : event.academic ? 'University calendar' : 'Official schedule';
      button.append(time, body, action); button.onclick = () => planner.editActivity(event.id); (event.academic?academicDetails:$('agendaEvents')).append(button);
    });
    if(day.events.some(e=>e.academic))$('agendaEvents').append(academicDetails);
  }
  $('agendaAdd').onclick = () => planner.addActivity(selectedDay);
  document.body.dataset.plannerView = 'dashboard';
  dashboardAgenda.hidden = false;
  $('hoursSummaryCard').hidden = true;
  dashboardAgenda.append(agenda);
  document.addEventListener('beacon:render', renderAgenda);
  renderAgenda();

  const academicBanner=document.createElement('details');academicBanner.className='academic-banner no-print';
  academicBanner.innerHTML='<summary><strong>University dates this week</strong><span id="academicCount"></span></summary><p id="academicStatus" role="status"></p><div id="academicWeekList"></div><a href="https://bushnell.edu/academics/academic-calendars/" target="_blank" rel="noopener">Official academic calendars ↗</a>';
  document.querySelector('.layout > .panel').append(academicBanner);
  function renderAcademicStatus(){
    const data=window.BeaconAcademic.status(),schedule=planner.getSchedule();
    const first=schedule.days[0].date,last=schedule.days.at(-1).date;
    const entries=(data.events||[]).filter(e=>e.start<=last&&e.end>first);
    $('academicCount').textContent=data.verified?entries.length+' dates'+(planner.getAcademicVisibility()?'':' · hidden from calendar'):'Unavailable';
    $('academicStatus').textContent=data.verified?[data.program,data.academicYear,'Check course-session labels.'].filter(Boolean).join(' · '):data.error||'University academic dates are not available yet.';
    $('academicWeekList').replaceChildren();
    for(const event of entries){
      const row=document.createElement('button');row.type='button';row.className='academic-date-row';
      const when=document.createElement('span');when.textContent=new Date(event.start+'T12:00:00').toLocaleDateString('en-US',{month:'short',day:'numeric'});
      const title=document.createElement('strong');title.textContent=event.title;
      row.append(when,title);row.onclick=()=>planner.editActivity(event.id);$('academicWeekList').append(row);
    }
    if(data.verified&&!entries.length)$('academicWeekList').textContent='No university dates listed for this week.';
  }
  document.addEventListener('beacon:academic',renderAcademicStatus);
  document.addEventListener('beacon:render',renderAcademicStatus);
  window.BeaconAcademic.load();

  const privacyPanel=document.createElement('details');privacyPanel.className='privacy-panel no-print';
  privacyPanel.innerHTML='<summary id="privacySummary">Privacy &amp; shared computers</summary><label class="privacy-choice"><input type="checkbox" id="privateSession">Private session — don’t save on this device</label><p id="privacyStatus" role="status"></p><p>Classes, names, goals, reminders, game check-in answers, and imported calendar files stay on this device. Sports schedules, academic dates, KJV verses, and reading references are included with the site; no outside data service receives your planner details. The hosting provider still receives connection information such as your IP address.</p><p>Saved entries are not encrypted in browser storage. Anyone using this browser profile may see them. Avoid sensitive IDs, grades, health details, or information about other students. Downloaded PDFs contain your schedule; share them carefully.</p><p>On a shared computer, use a private session, close other planner tabs, and close this page when finished. Private-session entries are lost on reload or when you close the page; this cannot erase existing downloads or other copies.</p>';
  document.querySelector('.toolbar').after(privacyPanel);
  function showPrivacy(){const state=window.BeaconPrivacy.status();$('privateSession').disabled=state.lockedPreview;$('privacySummary').textContent=state.privateMode?'Private session · changes are not saved':'Save on this device · on — privacy settings';$('privateSession').checked=state.privateMode;$('privacyStatus').textContent=state.erasureFailed?'This page will not save new entries, but it could not remove older browser data. Clear this site’s storage using your browser settings.':state.privateMode?'Private session: this planner is held only in this page and is not saved. Reloading or closing it discards these entries.':'Your changes save automatically in this browser and remain after refresh or closing. They do not sync to another device. Clearing browser data erases them. Use Clear all to erase this planner, or enable Private session on a shared computer.';}
  document.addEventListener('beacon:privacy',showPrivacy);showPrivacy();
  $('privateSession').onchange=()=>{
    const enabled=$('privateSession').checked;
    if(enabled&&!confirm('Switch to a private session? This removes the saved planner from this browser profile. Current entries stay in this page only and are lost on reload or close. Close other planner tabs on a shared computer.'))return showPrivacy();
    if(!enabled&&!confirm('Save this planner on this device? Anyone using this browser profile may be able to view it.'))return showPrivacy();
    window.BeaconPrivacy.setPrivate(enabled);planner.savePrivacyChoice();showPrivacy();
  };

  const verseCard = document.createElement('section'); verseCard.className = 'daily-verse-card';
  verseCard.innerHTML = '<span class="section-index">SCRIPTURE · KJV</span><h2>Verse of the day</h2><time id="verseDate"></time><blockquote id="verseText"></blockquote><a id="verseReference" target="_blank" rel="noopener"></a><p class="verse-note" id="verseCopyright"></p><p class="verse-note" id="verseStatus" role="status"></p><details class="daily-reading-plan"><summary>Today’s Bible reading</summary><div id="readingPassages"></div><a id="readingPlanSource" target="_blank" rel="noopener">About the yearly plan ↗</a></details><button class="verse-retry" id="verseRetry" type="button">Reload reading</button>';
  document.querySelector('.sidebar').prepend(verseCard);
  function renderVerse() {
    const verse = window.BeaconVerses.current(), status = window.BeaconVerses.status();
    $('verseDate').textContent = verse?.date || new Date().toLocaleDateString('en-US', {month:'long', day:'numeric', year:'numeric'});
    $('verseText').textContent = verse?.text || '';
    $('verseText').hidden = !verse;
    $('verseReference').textContent = verse ? verse.reference + ' · KJV' : 'Read the KJV Bible';
    $('verseReference').href = verse?.link || 'https://www.biblegateway.com/versions/King-James-Version-KJV-Bible/';
    $('verseCopyright').textContent = verse?.copyright || '';
    $('readingPassages').replaceChildren();
    if(verse){for(const passage of verse.passages){const link=document.createElement('a');link.textContent=passage;link.href='https://www.biblegateway.com/passage/?search='+encodeURIComponent(passage)+'&version=KJV';link.target='_blank';link.rel='noopener';$('readingPassages').append(link);}if(verse.catchUp)$('readingPassages').textContent='Leap-day catch-up: revisit any unfinished reading.';$('readingPlanSource').href=verse.planSource;}

    $('verseStatus').textContent = verse ? (verse.theme ? verse.theme[0].toUpperCase()+verse.theme.slice(1)+' · ' : '')+'Curated KJV passage; separate from the reading plan.' : status.state === 'loading' ? 'Loading saved reading content…' : status.error || 'Saved reading content is unavailable.';
    $('verseRetry').hidden = status.state !== 'error';
  }
  function updateVerse() {renderVerse(); window.BeaconVerses.load().then(renderVerse);}
  document.addEventListener('beacon:verse', renderVerse);
  $('verseRetry').onclick = () => window.BeaconVerses.load(true).then(renderVerse);
  let lastDay = window.BeaconVerses.dayKey();
  setInterval(() => {if (window.BeaconVerses.dayKey() !== lastDay) {lastDay = window.BeaconVerses.dayKey(); updateVerse();}}, 60000);
  window.addEventListener('focus', () => {if (window.BeaconVerses.dayKey() !== lastDay) {lastDay = window.BeaconVerses.dayKey(); updateVerse();}});
  document.addEventListener('visibilitychange', () => {if (!document.hidden && window.BeaconVerses.dayKey() !== lastDay) {lastDay = window.BeaconVerses.dayKey(); updateVerse();}});
  updateVerse();

  const modal = document.createElement('div'); modal.className = 'modal'; modal.id = 'exportDialog';
  modal.setAttribute('role', 'dialog'); modal.setAttribute('aria-modal', 'true'); modal.setAttribute('aria-labelledby', 'exportTitle');
  modal.innerHTML = `<div class="dialog export-dialog"><span class="section-index">SCHEDULE DOWNLOAD</span><h2 id="exportTitle">Print or download your schedule</h2><p class="sub">Export the week currently displayed, including personal activities and loaded competitions.</p><fieldset class="export-layouts"><legend>Choose a print layout</legend>
    <label><input type="radio" name="pdfLayout" value="grid" checked><span class="layout-thumbnail thumb-grid" aria-hidden="true"></span><strong>Weekly grid</strong><small>One landscape page. Compact blocks; long titles may shorten.</small></label>
    <label><input type="radio" name="pdfLayout" value="agenda"><span class="layout-thumbnail thumb-agenda" aria-hidden="true"></span><strong>Weekly agenda</strong><small>Portrait day lists with full activity names and locations.</small></label>
    <label><input type="radio" name="pdfLayout" value="daily"><span class="layout-thumbnail thumb-daily" aria-hidden="true"></span><strong>Daily pages</strong><small>A portrait page for each day, with space for written notes.</small></label>
    </fieldset><div class="export-options"><label>Paper size<select id="exportPaper"><option value="letter">US Letter</option><option value="a4">A4</option></select></label><label class="check-option"><input type="checkbox" id="exportGrayscale">Grayscale</label><label class="check-option"><input type="checkbox" id="exportVerse">Include today’s verse</label></div><p class="sub">PDFs are created on your device and contain your schedule. Store and share them carefully. Dense agendas can continue onto additional pages.</p><div class="error" id="exportError" role="status"></div><div class="actions"><button class="secondary" id="exportCancel">Cancel</button><button class="secondary" id="exportPreview">Preview / Print</button><button id="exportDownload">Download PDF</button></div></div>`;
  document.body.append(modal);
  let opener;
  const close = () => {modal.classList.remove('show'); opener?.focus();};
  $('print').onclick = () => {opener = document.activeElement; $('exportError').textContent = ''; modal.classList.add('show'); modal.querySelector('input:checked').focus();};
  $('exportCancel').onclick = close;
  modal.onclick = event => {if (event.target === modal) close();};
  modal.addEventListener('keydown', event => {
    if (event.key === 'Escape') {event.preventDefault(); close();}
    if (event.key === 'Tab') {
      const items = [...modal.querySelectorAll('button,input,select')].filter(e => !e.disabled);
      if (event.shiftKey && document.activeElement === items[0]) {event.preventDefault(); items.at(-1).focus();}
      else if (!event.shiftKey && document.activeElement === items.at(-1)) {event.preventDefault(); items[0].focus();}
    }
  });
  function exportPDF(preview) {
    try {
      const schedule = planner.getSchedule();
      const options = {layout: modal.querySelector('input[name="pdfLayout"]:checked').value, paper: $('exportPaper').value, grayscale: $('exportGrayscale').checked, includeVerse: $('exportVerse').checked};
      if (options.includeVerse && !schedule.verse) throw Error('Today’s saved verse has not loaded. Reload it or uncheck Include today’s verse.');
      const doc = window.BeaconPDF.build(schedule, options);
      if (preview) {
        const url = URL.createObjectURL(doc.output('blob'));
        const tab = window.open(url, '_blank');
        if (!tab) {URL.revokeObjectURL(url); throw Error('Allow this preview to open, or use Download PDF.');}
        tab.opener = null; setTimeout(() => URL.revokeObjectURL(url), 60000);
      } else doc.save(`Beacon-schedule-${schedule.weekKey}-${options.layout}.pdf`);
      $('exportError').textContent = '';
    } catch (error) {$('exportError').textContent = error.message || 'Unable to create the PDF.';}
  }
  $('exportDownload').onclick = () => exportPDF(false);
  $('exportPreview').onclick = () => exportPDF(true);
})();
