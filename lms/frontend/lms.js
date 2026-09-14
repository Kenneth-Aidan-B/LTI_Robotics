/* LTI LMS shared client */
const LMS = {
  get token(){ return localStorage.getItem('lti_token')||'' },
  set token(t){ t?localStorage.setItem('lti_token',t):localStorage.removeItem('lti_token') },
  get user(){ try{return JSON.parse(localStorage.getItem('lti_user')||'null')}catch{return null} },
  set user(u){ u?localStorage.setItem('lti_user',JSON.stringify(u)):localStorage.removeItem('lti_user') },
  async api(path, opts={}){
    const r = await fetch(path, {headers:{'Content-Type':'application/json',...(this.token?{Authorization:'Bearer '+this.token}:{})},...opts});
    const d = await r.json().catch(()=>({}));
    if(!r.ok){let m='HTTP '+r.status;if(typeof d.detail==='string')m=d.detail;else if(Array.isArray(d.detail))m=d.detail.map(x=>x.msg||JSON.stringify(x)).join('; ');else if(d.message)m=d.message;throw new Error(m)}
    return d;
  },
  logout(){ this.token=''; this.user=null; location.href='index.html' },
  guard(role){
    if(!this.token||!this.user){ location.href='auth.html'; return null }
    if(role && this.user.role!==role){ location.href = this.user.role==='admin'?'admin.html':'dashboard.html'; return null }
    return this.user;
  }
};
window.LMS = LMS;
