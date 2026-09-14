(()=>{ 
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
window.addEventListener('load',()=>setTimeout(()=>$('#preloader')?.classList.add('hide'),600));
setTimeout(()=>$('#preloader')?.classList.add('hide'),2500);

// mobile
$('#menuBtn')?.addEventListener('click',()=>{const m=$('#mobileMenu');m.classList.toggle('open');$('#menuBtn').setAttribute('aria-expanded',m.classList.contains('open'))});
$$('#mobileMenu a').forEach(a=>a.addEventListener('click',()=>{$('#mobileMenu').classList.remove('open');$('#menuBtn')?.setAttribute('aria-expanded','false')}));
window.addEventListener('resize',()=>{if(innerWidth>980)$('#mobileMenu')?.classList.remove('open')});
window.addEventListener('keydown',e=>{if(e.key==='Escape')$('#mobileMenu')?.classList.remove('open')});

// reveal + counters
if(!('IntersectionObserver' in window)){$$('.reveal').forEach(el=>el.classList.add('show'));$$('[data-count]').forEach(el=>el.textContent=el.dataset.count)}
else{
const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('show');io.unobserve(e.target)}}),{threshold:.12});
$$('.reveal').forEach(el=>io.observe(el));
const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
const cio=new IntersectionObserver(es=>es.forEach(e=>{if(!e.isIntersecting)return;const el=e.target,end=+el.dataset.count;if(reduced){el.textContent=end;cio.unobserve(el);return}let s=null;const step=t=>{if(!s)s=t;const p=Math.min(1,(t-s)/1200);el.textContent=Math.round(end*(1-Math.pow(1-p,3)));if(p<1)requestAnimationFrame(step)};requestAnimationFrame(step);cio.unobserve(el)}),{threshold:.6});
$$('[data-count]').forEach(el=>cio.observe(el));
}

// tabs
function selectTab(b){$$('.tab').forEach(x=>{x.classList.remove('active');x.setAttribute('aria-selected','false')});$$('.tab-panel').forEach(x=>{x.classList.remove('active');x.classList.remove('show')});b.classList.add('active');b.setAttribute('aria-selected','true');const p=document.getElementById(b.dataset.tab);p?.classList.add('active');p?.classList.add('show')}
$$('.tab').forEach(b=>b.addEventListener('click',()=>selectTab(b)));
function activateLvl(id){const t=document.querySelector(`.tab[data-tab="${id}"]`);if(!t)return;selectTab(t);document.getElementById('levels')?.scrollIntoView({behavior:'smooth',block:'start'})}
$$('a[href="#lvl1"],a[href="#lvl2"],a[href="#lvl3"]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();history.replaceState(null,'','#'+a.getAttribute('href').slice(1));activateLvl(a.getAttribute('href').slice(1))}));
if(location.hash && ['#lvl1','#lvl2','#lvl3'].includes(location.hash))activateLvl(location.hash.slice(1));
window.addEventListener('hashchange',()=>{if(['#lvl1','#lvl2','#lvl3'].includes(location.hash))activateLvl(location.hash.slice(1))});

// tilt + magnetic
$$('.tilt').forEach(card=>{card.addEventListener('mousemove',e=>{const r=card.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;card.style.transform=`perspective(900px) rotateX(${-y*8}deg) rotateY(${x*10}deg)`});card.addEventListener('mouseleave',()=>card.style.transform='')});
$$('.magnetic').forEach(b=>{b.addEventListener('mousemove',e=>{const r=b.getBoundingClientRect();b.style.transform=`translate(${(e.clientX-r.left-r.width/2)*.08}px,${(e.clientY-r.top-r.height/2)*.12}px)`});b.addEventListener('mouseleave',()=>b.style.transform='')});

function toast(m){const t=$('#toast');t.textContent=m;t.classList.add('show');clearTimeout(t._h);t._h=setTimeout(()=>t.classList.remove('show'),3200)}

// lead form
const form=$('#leadForm'), status=$('#formStatus'), prev=$('#leadPreview'), btn=$('#submitBtn');
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
form?.addEventListener('submit',async e=>{
 e.preventDefault();status.className='form-status';status.textContent='';
 const fd=new FormData(form);
 const lead={name:(fd.get('name')||'').toString().trim(),phone:(fd.get('phone')||'').toString().trim(),email:(fd.get('email')||'').toString().trim(),grade:fd.get('grade'),level:fd.get('level'),school:(fd.get('school')||'').toString().trim(),message:(fd.get('message')||'').toString().trim(),at:new Date().toISOString(),page:location.href};
 if(!lead.name||!lead.phone||!lead.email||!lead.grade||!lead.level){status.classList.add('err');status.textContent='Please fill Name, Phone, Email, Grade, Level.';return}
 const consent=form.querySelector('input[type="checkbox"]');
 if(consent&&!consent.checked){status.classList.add('err');status.textContent='Please accept contact consent.';return}
 if(!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(lead.email)){status.classList.add('err');status.textContent='Enter a valid reply-to email.';return}
 if(lead.phone.replace(/\D/g,'').length<7){status.classList.add('err');status.textContent='Enter a callable phone number.';return}
 btn.disabled=true;btn.textContent='Sending…';status.textContent='Creating lead…';
 const cfg=window.LTI_CONFIG||{};
 const text=`NEW LTI ROBOTICS LEAD\n\nName: ${lead.name}\nPhone: ${lead.phone} (tel:${lead.phone})\nEmail: ${lead.email} (reply-to)\nGrade: ${lead.grade}\nLevel: ${lead.level}\nSchool: ${lead.school||'-'}\nMsg: ${lead.message||'-'}\nAt: ${lead.at}\nPage: ${lead.page}`;
 let sent={lms:false,ext:false};
 try{const r=await fetch('/api/leads',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:lead.name,phone:lead.phone,email:lead.email,grade:lead.grade,level:lead.level,school:lead.school,message:lead.message})});sent.lms=r.ok}catch{}
 try{if(cfg.BACKEND_URL){const r=await fetch(cfg.BACKEND_URL,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...lead,replyTo:lead.email})});sent.ext=r.ok}}catch(err){console.warn('ext lead failed',err)}
 if(!sent.lms&&!sent.ext){try{const k='lti_leads';const arr=JSON.parse(localStorage.getItem(k)||'[]');if(!arr.some(x=>x.email===lead.email&&x.phone===lead.phone))arr.push(lead);localStorage.setItem(k,JSON.stringify(arr.slice(-50)))}catch{}}
 const adm=cfg.ADMISSIONS_EMAIL||'lti4official26@gmail.com';
 const subject=encodeURIComponent(`New Robotics Lead: ${lead.name} - ${lead.grade} - ${lead.level}`);
 const body=encodeURIComponent(`${text}\n\n--\nReply-To: ${lead.email}\nCall: ${lead.phone}`);
 if(!sent.lms&&!sent.ext){const a=document.createElement('a');a.href=`mailto:${adm}?subject=${subject}&body=${body}`;document.body.appendChild(a);a.click();a.remove()}
 const tel=lead.phone.replace(/[^+\d]/g,'');
 prev.classList.remove('hidden');
 prev.innerHTML=`<strong>✓ Lead captured${sent.lms?' in LMS':''}${sent.ext?' + sent to inbox':''}.</strong><br>👤 ${esc(lead.name)} · 🎓 ${esc(lead.grade)} · 🤖 ${esc(lead.level)}<br>📞 <a style="color:#FFC531" href="tel:${encodeURIComponent(tel)}">${esc(lead.phone)}</a> · ✉️ <a style="color:#FFC531" href="mailto:${esc(lead.email)}">${esc(lead.email)}</a><br><small>Admin can Call / Reply from Admin → Leads. ${sent.lms||sent.ext?'':'Saved locally.'}</small>`;
 status.classList.add('ok');status.textContent=sent.lms||sent.ext?'Enquiry sent to LTI. We will call/reply within 24 working hours.':'Saved locally + mail draft opened.';
 toast('Enquiry received ✓');form.reset();btn.disabled=false;btn.textContent='Submit Enquiry →';
});
})();
