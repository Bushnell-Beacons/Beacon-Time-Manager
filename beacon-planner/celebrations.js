/* Celebrations and student-reported game check-ins stay in the planner's local state. */
(() => {
 'use strict';
 const planner=window.BeaconPlanner,reduced=()=>window.matchMedia('(prefers-reduced-motion: reduce)').matches;
 let toastTimer=null,animationTimer=null,activeGame=null,answered=false,sessionSkip=null;
 const toast=document.createElement('section');toast.id='goalCelebration';toast.className='goal-celebration no-print';toast.hidden=true;toast.setAttribute('role','status');toast.setAttribute('aria-live','polite');
 toast.innerHTML='<span class="celebration-check" aria-hidden="true">✓</span><div><strong>Goal completed!</strong><p></p></div><button type="button" aria-label="Dismiss goal celebration">×</button>';document.body.append(toast);
 const dialog=document.createElement('dialog');dialog.id='gameCheckin';dialog.className='win-celebration game-checkin';dialog.setAttribute('aria-labelledby','gameCheckinTitle');dialog.setAttribute('aria-describedby','gameCheckinDetail');
 dialog.innerHTML='<div class="win-emblem" aria-hidden="true">★</div><h2 id="gameCheckinTitle">How did your game go?</h2><p id="gameCheckinDetail"></p><p class="game-checkin-date"></p><div class="game-outcome-options"><button type="button" class="gold" data-outcome="win">We won</button><button type="button" class="secondary" data-outcome="loss">We lost</button><button type="button" class="secondary" data-outcome="tie">Draw / tie</button></div><p class="game-feedback" role="status" hidden></p><div class="game-feedback-actions" hidden><button type="button" class="gold game-done">Back to my planner</button><button type="button" class="secondary game-change">Change answer</button></div><div class="game-checkin-later"><button type="button" class="secondary game-later">Ask me in an hour</button><button type="button" class="secondary game-skip">Skip this game</button></div><p class="game-checkin-note">Game still going? Choose “Ask me in an hour.” Your answer stays in this browser.</p>';document.body.append(dialog);
 const confetti=document.createElement('div');confetti.className='celebration-confetti no-print';confetti.setAttribute('aria-hidden','true');document.body.append(confetti);
 function burst(){clearTimeout(animationTimer);confetti.replaceChildren();if(reduced())return;for(let i=0;i<24;i++){const piece=document.createElement('i');piece.style.setProperty('--x',(8+Math.random()*84)+'vw');piece.style.setProperty('--drift',(-70+Math.random()*140)+'px');piece.style.setProperty('--delay',(Math.random()*.2)+'s');piece.style.setProperty('--spin',(-160+Math.random()*320)+'deg');piece.style.background=['#c99b42','#172b47','#87c5f4'][i%3];confetti.append(piece);}animationTimer=setTimeout(()=>confetti.replaceChildren(),1800);}
 function hideGoal(){clearTimeout(toastTimer);toast.hidden=true;}
 toast.querySelector('button').onclick=hideGoal;
 document.addEventListener('beacon:goal-completed',event=>{toast.querySelector('p').textContent=String(event.detail?.text||'');toast.hidden=false;burst();clearTimeout(toastTimer);toastTimer=setTimeout(hideGoal,5000);});
 function prompt(){
  dialog.querySelector('h2').textContent='How did your game go?';dialog.querySelector('.win-emblem').textContent='★';dialog.querySelector('.game-outcome-options').hidden=false;dialog.querySelector('.game-checkin-later').hidden=false;dialog.querySelector('.game-feedback').hidden=true;dialog.querySelector('.game-feedback-actions').hidden=true;dialog.querySelector('.game-checkin-note').hidden=false;
  dialog.querySelector('#gameCheckinDetail').textContent='Bushnell vs. '+activeGame.title;
  dialog.querySelector('.game-checkin-date').textContent=new Date(activeGame.start).toLocaleDateString('en-US',{month:'long',day:'numeric',year:'numeric'});
 }
 function postpone(){if(!activeGame)return;planner.saveGameCheckin(activeGame.id,{snoozedUntil:Date.now()+60*60*1000});dialog.close();}
 dialog.querySelector('.game-later').onclick=postpone;
 dialog.querySelector('.game-skip').onclick=()=>{if(activeGame)planner.saveGameCheckin(activeGame.id,{outcome:'skip',answeredAt:Date.now()});dialog.close();};
 for(const button of dialog.querySelectorAll('[data-outcome]'))button.onclick=()=>{
  if(!activeGame)return;const outcome=button.dataset.outcome;planner.saveGameCheckin(activeGame.id,{outcome,answeredAt:Date.now()});answered=true;
  const feedback={win:['Beacons win!','Enjoy the win and recognize the work you put in.','★'],loss:['Keep going, Beacon.','One game doesn’t define your progress. Recover, reflect, and focus on your next opportunity.','◆'],tie:['Keep building.','Take what you learned today into your next game.','◆']}[outcome];
  dialog.querySelector('h2').textContent=feedback[0];dialog.querySelector('.win-emblem').textContent=feedback[2];dialog.querySelector('.game-feedback').textContent=feedback[1];dialog.querySelector('.game-feedback').hidden=false;dialog.querySelector('.game-outcome-options').hidden=true;dialog.querySelector('.game-checkin-later').hidden=true;dialog.querySelector('.game-checkin-note').hidden=true;dialog.querySelector('.game-feedback-actions').hidden=false;dialog.querySelector('.game-done').focus();if(outcome==='win')burst();else{clearTimeout(animationTimer);confetti.replaceChildren();}
 };
 dialog.querySelector('.game-done').onclick=()=>dialog.close();dialog.querySelector('.game-change').onclick=()=>{prompt();dialog.querySelector('[data-outcome="win"]').focus();};
 dialog.addEventListener('cancel',event=>{event.preventDefault();if(answered)dialog.close();else postpone();});
 dialog.addEventListener('close',()=>{activeGame=null;answered=false;});
 function checkGames(){
  if(document.visibilityState==='hidden'||dialog.open||document.querySelector('dialog[open],.modal.show'))return;
  const state=planner.getGameCheckinState(),game=state.games[0];if(!game||game.id===sessionSkip)return;
  const response=state.responses[game.id];if(response?.outcome||response?.snoozedUntil>Date.now())return;
  activeGame=game;answered=false;prompt();dialog.showModal();sessionSkip=game.id;
 }
 document.addEventListener('beacon:render',()=>{sessionSkip=null;checkGames();});document.addEventListener('visibilitychange',()=>{sessionSkip=null;checkGames();});setInterval(()=>{sessionSkip=null;checkGames();},60000);checkGames();
 window.addEventListener('pagehide',()=>{hideGoal();if(dialog.open)dialog.close();confetti.replaceChildren();});
})();
