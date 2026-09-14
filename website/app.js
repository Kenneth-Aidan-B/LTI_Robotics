(()=>{ 
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
window.addEventListener('load',()=>setTimeout(()=>$('#preloader')?.classList.add('hide'),600));
setTimeout(()=>$('#preloader')?.classList.add('hide'),2500);

// mobile
$('#menuBtn')?.addEventListener('click',()=>$('#mobileMenu').classList.toggle('open'));
$$('#mobileMenu a').forEach(a=>a.addEventListener('click',()=>$('#mobileMenu').classList.remove('open')));

// reveal + counters
const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('show');io.unobserve(e.target)}}),{threshold:.12});
$$('.reveal').forEach(el=>io.observe(el));
const cio=new IntersectionObserver(es=>es.forEach(e=>{if(!e.isIntersecting)return;const el=e.target,end=+el.dataset.count;let s=null;const step=t=>{if(!s)s=t;const p=Math.min(1,(t-s)/1200);el.textContent=Math.round(end*(1-Math.pow(1-p,3)));if(p<1)requestAnimationFrame(step)};requestAnimationFrame(step);cio.unobserve(el)}),{threshold:.6});
$$('[data-count]').forEach(el=>cio.observe(el));

// tabs
$$('.tab').forEach(b=>b.addEventListener('click',()=>{$$('.tab').forEach(x=>x.classList.remove('active'));$$('.tab-panel').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.getElementById(b.dataset.tab)?.classList.add('active')}));
function activateLvl(id){const t=document.querySelector(`.tab[data-tab="${id}"]`);if(!t)return;$$('.tab').forEach(x=>x.classList.remove('active'));$$('.tab-panel').forEach(x=>x.classList.remove('active'));t.classList.add('active');document.getElementById(id)?.classList.add('active')}
$$('a[href="#lvl1"],a[href="#lvl2"],a[href="#lvl3"]').forEach(a=>a.addEventListener('click',()=>activateLvl(a.getAttribute('href').slice(1))));
if(location.hash && ['#lvl1','#lvl2','#lvl3'].includes(location.hash))activateLvl(location.hash.slice(1));
window.addEventListener('hashchange',()=>{if(['#lvl1','#lvl2','#lvl3'].includes(location.hash))activateLvl(location.hash.slice(1))});

// tilt + magnetic
$$('.tilt').forEach(card=>{card.addEventListener('mousemove',e=>{const r=card.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;card.style.transform=`perspective(900px) rotateX(${-y*8}deg) rotateY(${x*10}deg)`});card.addEventListener('mouseleave',()=>card.style.transform='')});
$$('.magnetic').forEach(b=>{b.addEventListener('mousemove',e=>{const r=b.getBoundingClientRect();b.style.transform=`translate(${(e.clientX-r.left-r.width/2)*.08}px,${(e.clientY-r.top-r.height/2)*.12}px)`});b.addEventListener('mouseleave',()=>b.style.transform='')});

function toast(m){const t=$('#toast');t.textContent=m;t.classList.add('show');clearTimeout(t._h);t._h=setTimeout(()=>t.classList.remove('show'),3200)}

// lead form
const form=$('#leadForm'), status=$('#formStatus'), prev=$('#leadPreview'), btn=$('#submitBtn');
function esc(s){return String(s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
form?.addEventListener('submit',async e=>{
 e.preventDefault();status.className='form-status';status.textContent='';
 const fd=new FormData(form);
 const lead={name:(fd.get('name')||'').toString().trim(),phone:(fd.get('phone')||'').toString().trim(),email:(fd.get('email')||'').toString().trim(),grade:fd.get('grade'),level:fd.get('level'),school:(fd.get('school')||'').toString().trim(),message:(fd.get('message')||'').toString().trim(),at:new Date().toISOString(),page:location.href};
 if(!lead.name||!lead.phone||!lead.email||!lead.grade||!lead.level){status.classList.add('err');status.textContent='Please fill Name, Phone, Email, Grade, Level.';return}
 if(!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(lead.email)){status.classList.add('err');status.textContent='Enter a valid reply-to email.';return}
 if(lead.phone.replace(/\D/g,'').length<7){status.classList.add('err');status.textContent='Enter a callable phone number.';return}
 btn.disabled=true;btn.textContent='Sending…';status.textContent='Creating lead…';
 const cfg=window.LTI_CONFIG||{};
 const text=`🚀 NEW LTI ROBOTICS LEAD\n\n👤 ${lead.name}\n📞 ${lead.phone} (tap to call: tel:${lead.phone})\n✉️ ${lead.email} (reply-to)\n🎓 Grade: ${lead.grade}\n🤖 Level: ${lead.level}\n🏫 School: ${lead.school||'-'}\n💬 ${lead.message||'-'}\n🕒 ${lead.at}\n🌐 ${lead.page}`;
 let sent={backend:false,telegram:false};
 try{
  if(cfg.BACKEND_URL){const r=await fetch(cfg.BACKEND_URL,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...lead,replyTo:lead.email})});sent.backend=r.ok}
  if(!sent.backend&&cfg.TELEGRAM_BOT_TOKEN&&cfg.TELEGRAM_CHAT_ID){
   const r=await fetch(`https://api.telegram.org/bot${cfg.TELEGRAM_BOT_TOKEN}/sendMessage`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({chat_id:cfg.TELEGRAM_CHAT_ID,text,parse_mode:'HTML'})});
   sent.telegram=r.ok;
  }
 }catch(err){console.warn('lead send failed, fallback',err)}
 try{const k='lti_leads';const arr=JSON.parse(localStorage.getItem(k)||'[]');arr.push(lead);localStorage.setItem(k,JSON.stringify(arr))}catch{}
 // always open mail draft so receiver can Call / Reply
 const adm=cfg.ADMISSIONS_EMAIL||'lti4official26@gmail.com';
 const subject=encodeURIComponent(`New Robotics Lead: ${lead.name} · ${lead.grade} · ${lead.level}`);
 const body=encodeURIComponent(`${text}\n\n--\nReply-To: ${lead.email}\nCall: ${lead.phone}`);
 if(!cfg.BACKEND_URL&&!cfg.TELEGRAM_BOT_TOKEN){window.location.href=`mailto:${adm}?reply-to=${encodeURIComponent(lead.email)}&subject=${subject}&body=${body}`}
 prev.classList.remove('hidden');
 prev.innerHTML=`<strong>✓ Lead captured${sent.backend||sent.telegram?' + sent to inbox/Telegram':''}.</strong><br>👤 ${esc(lead.name)} · 🎓 ${esc(lead.grade)} · 🤖 ${esc(lead.level)}<br>📞 <a style="color:#FFC531" href="tel:${esc(lead.phone)}">${esc(lead.phone)}</a> · ✉️ <a style="color:#FFC531" href="mailto:${esc(lead.email)}">${esc(lead.email)}</a><br><small>Add keys in config.js later to auto-post without mail draft.</small>`;
 status.classList.add('ok');status.textContent=sent.backend||sent.telegram?'Enquiry sent. We will call/reply within 24 working hours.':'Saved locally + mail draft opened. Add backend keys to auto-send.';
 toast('Enquiry received ✓');form.reset();btn.disabled=false;btn.textContent='Submit Enquiry →';
});
})();
