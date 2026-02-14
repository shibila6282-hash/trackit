document.addEventListener('DOMContentLoaded', ()=>{
  // Dark mode toggle
  const darkToggle = document.getElementById('darkToggle');
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const saved = localStorage.getItem('trackit-dark');
  if(saved === '1' || (!saved && prefersDark)) document.body.classList.add('dark');

  darkToggle && darkToggle.addEventListener('click', ()=>{
    const isDark = document.body.classList.toggle('dark');
    localStorage.setItem('trackit-dark', isDark ? '1' : '0');
  });

  /* --- Day Chips: Interactive filtering --- */
  const dayChips = document.getElementById('dayChips');
  const habitsContainer = document.querySelector('.habits');
  const allChips = document.querySelectorAll('.chip');
  let selectedDay = 2; // Wednesday by default (today)

  function filterHabitsByDay(dayOfWeek) {
    const cards = document.querySelectorAll('.habit-card');
    let visibleCount = 0;
    
    cards.forEach(card => {
      if (dayOfWeek === null) {
        // Show all habits
        card.style.display = '';
        card.classList.add('animate-in');
      } else {
        // For now, show all cards (future: could use card data to determine day)
        card.style.display = '';
        card.classList.add('animate-in');
        visibleCount++;
      }
    });
  }

  if (dayChips) {
    allChips.forEach(chip => {
      chip.addEventListener('click', (e) => {
        e.preventDefault();
        
        // Remove active class from all chips
        allChips.forEach(c => c.classList.remove('active'));
        
        // Add active class to clicked chip
        chip.classList.add('active');
        
        // Get the day number
        selectedDay = parseInt(chip.getAttribute('data-day'), 10);
        
        // Animate habit cards
        const cards = document.querySelectorAll('.habit-card');
        cards.forEach((card, idx) => {
          card.style.animation = 'none';
          setTimeout(() => {
            card.style.animation = 'fadeInScale 0.3s ease-out forwards';
            card.style.animationDelay = `${idx * 0.05}s`;
          }, 10);
        });
        
        // Save preference
        localStorage.setItem('trackit-selected-day', selectedDay);
      });
    });

    // Restore saved day preference
    const savedDay = localStorage.getItem('trackit-selected-day');
    if (savedDay !== null) {
      selectedDay = parseInt(savedDay, 10);
      allChips.forEach(chip => {
        const chipDay = parseInt(chip.getAttribute('data-day'), 10);
        if (chipDay === selectedDay) {
          chip.classList.add('active');
        } else {
          chip.classList.remove('active');
        }
      });
    }
  }

  // Handle Done micro-interaction: animate then submit
  // When the user marks a habit Done, show flame animation then send request
  document.querySelectorAll('.doneForm').forEach(form=>{
    form.addEventListener('submit', async (e)=>{
      e.preventDefault();
      const btn = form.querySelector('.btn.done');
      if(!btn) return form.submit();
      btn.classList.add('animate');
      btn.disabled = true;

      // show streak flame on the card
      const card = form.closest('.habit-card');
      const flame = card && card.querySelector('.flame');
      if(flame){
        flame.classList.remove('pop');
        // trigger reflow to restart
        void flame.offsetWidth;
        flame.classList.add('pop');
      }

      // small delay to let the animation feel satisfying
      await new Promise(r=>setTimeout(r, 520));

      try{
        const data = new FormData(form);
        await fetch(form.action, {method:'POST', body:data});
        // brief success pulse
        btn.textContent = '✓';
        setTimeout(()=>{ location.reload(); }, 600);
      }catch(err){
        btn.classList.remove('animate');
        btn.disabled = false;
      }
    });
  });

  // Handle Skip button: submit and reload
  document.querySelectorAll('.skipForm').forEach(form=>{
    form.addEventListener('submit', async (e)=>{
      e.preventDefault();
      const btn = form.querySelector('.btn.skip');
      if(!btn) return form.submit();
      btn.disabled = true;
      btn.textContent = '⊘ Skipped';
      btn.style.opacity = '0.6';

      await new Promise(r=>setTimeout(r, 300));

      try{
        const data = new FormData(form);
        await fetch(form.action, {method:'POST', body:data});
        setTimeout(()=>{ location.reload(); }, 400);
      }catch(err){
        btn.disabled = false;
        btn.textContent = 'Skip';
        btn.style.opacity = '1';
      }
    });
  });

  // Handle Edit button: open modal
  document.querySelectorAll('.edit-btn').forEach(btn=>{
    btn.addEventListener('click', (e)=>{
      e.preventDefault();
      const habitName = btn.getAttribute('data-habit');
      const habitId = habitName.replace(/\s+/g, '-');
      const modal = document.getElementById(`edit-${habitId}`);
      if(modal){
        modal.style.display = 'flex';
        const input = modal.querySelector('input[name="new_name"]');
        if(input) input.focus();
      }
    });
  });

  // Handle Cancel button in modal
  document.querySelectorAll('.cancel-modal').forEach(btn=>{
    btn.addEventListener('click', (e)=>{
      e.preventDefault();
      const modal = btn.closest('.edit-modal');
      if(modal) modal.style.display = 'none';
    });
  });

  // Close modal on outside click
  document.querySelectorAll('.edit-modal').forEach(modal=>{
    modal.addEventListener('click', (e)=>{
      if(e.target === modal) modal.style.display = 'none';
    });
  });

  // Handle Delete button with confirmation
  document.querySelectorAll('.deleteForm').forEach(form=>{
    form.addEventListener('submit', (e)=>{
      e.preventDefault();
      const habitName = form.querySelector('input[name="name"]').value;
      if(confirm(`Are you sure you want to delete "${habitName}"? This action cannot be undone.`)){
        form.submit();
      }
    });
  });

  // Handle Edit form submission
  document.querySelectorAll('.edit-modal form').forEach(form=>{
    form.addEventListener('submit', (e)=>{
      e.preventDefault();
      const newName = form.querySelector('input[name="new_name"]').value.trim();
      const oldName = form.querySelector('input[name="old_name"]').value;
      
      if(newName && newName !== oldName){
        form.submit();
      } else if(newName === oldName){
        // Close modal without change
        const modal = form.closest('.edit-modal');
        if(modal) modal.style.display = 'none';
      }
    });
  });

  // Load weekly chart
  async function loadWeekly(){
    try{
      const res = await fetch('/weekly');
      const data = await res.json();
      const ctx = document.getElementById('weeklyChart');
      if(!ctx) return;
      new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
          labels: data.dates,
          datasets: [{
            label: 'Success Rate (%)',
            data: data.values,
            borderColor: getComputedStyle(document.documentElement).getPropertyValue('--accent-blue').trim() || '#2ca7a1',
            backgroundColor: 'rgba(76,125,255,0.08)',
            tension: 0.35,
            fill: true,
            pointRadius: 3
          }]
        },
        options: {
          plugins:{legend:{display:false}},
          scales:{y:{min:0,max:100,ticks:{color:getComputedStyle(document.body).color}} , x:{ticks:{color:getComputedStyle(document.body).color}}}
        }
      });
    }catch(e){ console.warn('Weekly chart load failed', e); }
  }
  loadWeekly();

  // FAB: focus the add input
  const fab = document.getElementById('fab');
  if(fab){
    fab.addEventListener('click', ()=>{
      const input = document.querySelector('#addForm input[name="name"]');
      if(input){ input.focus(); input.scrollIntoView({behavior:'smooth',block:'center'}); }
    });
  }

  /* --- Progressive visual enhancements --- */
  // Entrance animation for habit cards (staggered)
  const cards = Array.from(document.querySelectorAll('.habit-card'));
  cards.forEach((c,i)=>{
    setTimeout(()=> c.classList.add('enter'), 90 * i);
  });

  // Animate progress circles from 0 -> target percent using small JS tween
  function animateProgress(el, target){
    let current = 0;
    const step = Math.max(1, Math.floor(target / 20));
    const interval = setInterval(()=>{
      current = Math.min(target, current + step);
      const deg = Math.round((current / 100) * 360);
      // choose accent color depending on theme
      const accent = getComputedStyle(document.documentElement).getPropertyValue('--accent-teal').trim() || '#2bb6af';
      const bg = getComputedStyle(document.documentElement).getPropertyValue('--surface').trim() || '#0b1220';
      el.style.background = `conic-gradient(${accent} ${deg}deg, ${bg} ${deg}deg)`;
      const label = el.parentElement.querySelector('.progress-label');
      if(label) label.textContent = `${current}%`;
      if(current >= target) clearInterval(interval);
    }, 14);
  }

  document.querySelectorAll('.habit-card').forEach(card=>{
    const prog = card.querySelector('.progress');
    const target = parseInt(card.getAttribute('data-rate') || 0, 10);
    if(prog){
      // start a little after entrance for nicer effect
      setTimeout(()=> animateProgress(prog, target), 220);
    }
  });

  // hero ring animation
  const heroRing = document.querySelector('.glow-ring .ring');
  if(heroRing){
    const v = parseInt(heroRing.getAttribute('data-value') || heroRing.dataset.value || 0,10);
    setTimeout(()=> animateProgress(heroRing, v), 260);
    // update hero label color for light on dark
    const label = document.querySelector('.glow-ring .ring-label');
    if(label) label.textContent = `${v}%`;
  }

  // Leaderboard: fetch and render
  async function fetchLeaderboard(){
    try{
      const res = await fetch('/leaderboard');
      const data = await res.json();
      const list = document.getElementById('leaderboardList');
      if(!list) return;
      list.innerHTML = '';
      const current = (document.body.dataset.user || '').trim();
      (data.top || []).forEach((row, idx)=>{
        const li = document.createElement('li');
        li.className = 'leader-row';
        if(current && row.user_name === current) li.classList.add('me');
        // compute initials for avatar
        const initials = (row.user_name || '').split(/\s+/).filter(Boolean).slice(0,2).map(s=>s[0].toUpperCase()).join('') || 'U';
        li.innerHTML = `<div class="left"><div class="rank">${idx+1}</div><div class="avatar-sm">${initials}</div><div class="who">${row.user_name}</div></div><div class="score">${row.score}</div>`;
        list.appendChild(li);
      });
      if((data.top || []).length === 0){
        list.innerHTML = '<li class="muted">No entries yet — be the first!</li>';
      }
    }catch(e){ console.warn('Failed to load leaderboard', e); }
  }
  fetchLeaderboard();

  // Edit user name UI: toggle inline edit form
  const editBtn = document.getElementById('editNameBtn');
  const editForm = document.getElementById('editNameForm');
  const cancelEdit = document.getElementById('cancelEditName');
  if(editBtn && editForm){
    editBtn.addEventListener('click', ()=>{
      editForm.style.display = 'flex';
      const input = editForm.querySelector('input[name="user_name"]');
      if(input){ input.focus(); input.select(); }
    });
  }
  if(cancelEdit && editForm){
    cancelEdit.addEventListener('click', ()=>{ editForm.style.display = 'none'; });
  }

  /* Calendar rendering: fetch month data and draw a simple heatmap calendar */
  const calGrid = document.getElementById('calendarGrid');
  const calLabel = document.getElementById('calLabel');
  const calPrev = document.getElementById('calPrev');
  const calNext = document.getElementById('calNext');
  let calDate = new Date(); // current month

  function monthKey(d){ return `${d.getFullYear()}-${d.getMonth()+1}`; }

  async function loadCalendar(date){
    const m = date.getMonth()+1; const y = date.getFullYear();
    calLabel.textContent = date.toLocaleString(undefined,{month:'long', year:'numeric'});
    try{
      // request only the current user's events by default
      const res = await fetch(`/calendar_data?month=${m}&year=${y}&user=me`);
      const js = await res.json();
      renderCalendar(date, js.counts || {}, js.max || 0);
    }catch(e){ console.warn('Calendar load failed', e); }
  }

  function renderCalendar(date, counts, maxv){
    if(!calGrid) return;
    calGrid.innerHTML = '';
    // weekday headers
    const weekdays = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
    weekdays.forEach(w=>{
      const h = document.createElement('div'); 
      h.className='cal-day'; 
      h.style.fontWeight='700';
      h.style.textAlign='center';
      h.style.color='var(--text)';
      h.style.background='rgba(139,111,71,0.1)';
      h.style.borderRadius='8px';
      h.textContent = w; 
      calGrid.appendChild(h);
    });

    const year = date.getFullYear(); const month = date.getMonth();
    const first = new Date(year, month, 1);
    const last = new Date(year, month+1, 0);
    const lead = first.getDay();
    // leading blanks
    for(let i=0;i<lead;i++){ 
      const e=document.createElement('div'); 
      e.className='cal-day';
      e.style.opacity='0.3';
      calGrid.appendChild(e); 
    }
    for(let d=1; d<= last.getDate(); d++){
      const cell = document.createElement('div'); 
      cell.className='cal-day';
      const num = document.createElement('div'); 
      num.className='num'; 
      num.textContent = d; 
      cell.appendChild(num);
      
      // Ensure we access counts with string key
      const cnt = counts[String(d)] || counts[d] || 0;
      const heat = document.createElement('div'); 
      heat.className='cal-heat';
      // compute opacity based on maxv using brown tones
      const op = maxv>0 ? Math.min(0.95, 0.15 + (cnt/maxv)*0.75) : 0.08;
      heat.style.background = `linear-gradient(180deg, rgba(209,114,87,${op}), rgba(155,125,95,${op}))`;
      heat.style.minHeight = '50px';
      heat.style.borderRadius = '8px';
      heat.innerHTML = `<div style="flex:1"></div><div style="font-size:11px;color:rgba(61,40,23,0.7);font-weight:600">${cnt>0?cnt+' ✓':''}</div>`;
      cell.appendChild(heat);
      calGrid.appendChild(cell);
    }
  }

  calPrev && calPrev.addEventListener('click', ()=>{ calDate = new Date(calDate.getFullYear(), calDate.getMonth()-1, 1); loadCalendar(calDate); });
  calNext && calNext.addEventListener('click', ()=>{ calDate = new Date(calDate.getFullYear(), calDate.getMonth()+1, 1); loadCalendar(calDate); });
  loadCalendar(calDate);

  /* --- Chat assistant UI --- */
  // inject chat controls into DOM
  const chatFab = document.createElement('button');
  chatFab.className = 'chat-fab';
  chatFab.id = 'chatFab';
  chatFab.title = 'Ask TrackIt Assistant';
  chatFab.innerHTML = '💬';
  document.body.appendChild(chatFab);

  const chatPanel = document.createElement('div');
  chatPanel.className = 'chat-panel';
  chatPanel.id = 'chatPanel';
  chatPanel.innerHTML = `
    <div class="chat-header"><div class="title">TrackIt Assistant</div><div style="margin-left:auto;font-size:14px;opacity:0.85">AI</div></div>
    <div class="chat-body" id="chatBody"></div>
    <div class="chat-footer">
      <input id="chatInput" class="chat-input" placeholder="Ask for habit tips, motivation..." />
      <button id="chatSend" class="chat-send">Send</button>
    </div>
  `;
  document.body.appendChild(chatPanel);

  const chatBody = document.getElementById('chatBody');
  const chatInput = document.getElementById('chatInput');
  const chatSend = document.getElementById('chatSend');

  function appendMessage(text, who){
    const wrap = document.createElement('div');
    wrap.className = 'msg ' + (who === 'user' ? 'user' : 'ai');
    const bubble = document.createElement('div');
    bubble.className = 'bubble ' + (who === 'user' ? 'user' : 'ai');
    bubble.textContent = text;
    wrap.appendChild(bubble);
    chatBody.appendChild(wrap);
    chatBody.scrollTop = chatBody.scrollHeight + 200;
  }

  function showTyping(){
    const t = document.createElement('div'); t.className = 'msg ai typing-wrap';
    t.innerHTML = `<div class="typing"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>`;
    chatBody.appendChild(t);
    chatBody.scrollTop = chatBody.scrollHeight + 200;
    return t;
  }

  async function sendChat(){
    const txt = (chatInput.value || '').trim();
    if(!txt) return;
    appendMessage(txt, 'user');
    chatInput.value = '';
    chatInput.disabled = true; chatSend.disabled = true;
    const typingNode = showTyping();
    try{
      const res = await fetch('/api/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({message: txt})});
      const js = await res.json();
      if(typingNode && typingNode.parentNode) typingNode.parentNode.removeChild(typingNode);
      if(js && js.reply){
        appendMessage(js.reply, 'ai');
      }else if(js && js.error){
        appendMessage('Assistant error: ' + (js.error || 'unknown'), 'ai');
      }else{
        appendMessage('No response from assistant.', 'ai');
      }
    }catch(e){
      if(typingNode && typingNode.parentNode) typingNode.parentNode.removeChild(typingNode);
      appendMessage('Network error contacting assistant.', 'ai');
    }finally{
      chatInput.disabled = false; chatSend.disabled = false; chatInput.focus();
    }
  }

  chatFab.addEventListener('click', ()=>{
    chatPanel.classList.toggle('open');
    if(chatPanel.classList.contains('open')) chatInput.focus();
  });
  chatSend.addEventListener('click', sendChat);
  chatInput.addEventListener('keydown', (e)=>{ if(e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); } });
});

function showReward(message) {
    document.getElementById("rewardText").innerText = message;
    document.getElementById("rewardModal").style.display = "flex";

    confetti({
        particleCount: 150,
        spread: 70,
        origin: { y: 0.6 }
    });
}

function closeReward() {
    document.getElementById("rewardModal").style.display = "none";
}
