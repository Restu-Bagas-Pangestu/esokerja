// Esokerja front end — ported from the Loker Sarjana review page (public view only).
(function(){
  const $=s=>document.querySelector(s);
  const BASE=document.body.dataset.base||"/";
  const MONTHS=["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agu","Sep","Okt","Nov","Des"];
  const DEG_ORDER=["SMA","SMK","D3","D4","S1","S2","S3"];
  const DEG_BASE=["D3","D4","S1","S2"];
  const ICON={
    pin:'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21Z"/><circle cx="12" cy="9.5" r="2.5"/></svg>',
    cap:'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m2 9 10-5 10 5-10 5L2 9Z"/><path d="M6 11v5c3 2.5 9 2.5 12 0v-5"/></svg>',
    bag:'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>',
    home:'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M3 11 12 4l9 7"/><path d="M5 10v10h14V10"/></svg>',
    x:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>'
  };
  // Today's date in WIB (UTC+7), where deadlines are set
  const _w=new Date(Date.now()+7*3600e3);
  const TODAY=_w.getUTCFullYear()+"-"+String(_w.getUTCMonth()+1).padStart(2,"0")+"-"+String(_w.getUTCDate()).padStart(2,"0");

  function fmtDate(s){ if(!s||!/^\d{4}-\d{2}-\d{2}/.test(s)) return ""; const [y,m,dd]=s.slice(0,10).split("-"); return (+dd)+" "+MONTHS[+m-1]+" "+y; }
  function daysLeft(s){ if(!s||!/^\d{4}-\d{2}-\d{2}/.test(s)) return null; return Math.round((new Date(s.slice(0,10)+"T00:00:00Z")-new Date(TODAY+"T00:00:00Z"))/864e5); }
  function safeUrl(u){ return typeof u==="string"&&/^https?:\/\//i.test(u)?u:null; }
  function el(tag,cls,text){ const e=document.createElement(tag); if(cls) e.className=cls; if(text!=null) e.textContent=text; return e; }
  function iconSpan(icon,text){ const s=el("span"); s.innerHTML=ICON[icon]; s.append(document.createTextNode(text)); return s; }

  function deadlinePill(job){
    const n=daysLeft(job.deadline);
    if(n===null) return el("span","pill p-none","Batas tidak disebut");
    if(n<0) return el("span","pill p-exp","Ditutup");
    if(n<=7) return el("span","pill p-soon",n===0?"Tutup hari ini":"Tutup "+n+" hari lagi");
    return el("span","pill p-open","s.d. "+fmtDate(job.deadline));
  }

  // Static job page: refresh the deadline pill to the reader's date, show the closed banner if needed.
  const jobPage=$("[data-job-deadline]");
  if(jobPage){
    const dl=jobPage.getAttribute("data-job-deadline");
    const slot=$("#deadlinePill"); if(slot){ slot.replaceWith(deadlinePill({deadline:dl})); }
    const n=daysLeft(dl); const b=$("#closed"); if(b) b.hidden=!(n!==null&&n<0);
  }

  const dataEl=$("#jobs-data");
  if(!dataEl) return;
  let JOBS=[]; try{ JOBS=JSON.parse(dataEl.textContent)||[]; }catch(e){}

  function degs(j){ const s=String(j.degree||"").toUpperCase().replace(/([SD])-(\d)/g,"$1$2"); return DEG_ORDER.filter(k=>new RegExp("(^|[^A-Z0-9])"+k+"([^A-Z0-9]|$)").test(s)); }
  const ALL_LABEL="Semua jurusan", ALL_VAL="__all";
  const ALL_RE=/semua jurusan|segala jurusan|seluruh jurusan|semua program studi|semua bidang studi|bidang studi apa ?pun|jurusan apa ?pun|all majors|any major|all disciplines/i;
  const EDU_LINE=/\b(s-?1|s-?2|s-?3|d-?3|d-?4|jurusan|program studi|prodi|lulusan|sarjana|bachelor|degree|graduate)\b/i;
  const MAJORS=[
    ["Teknik Mesin",/teknik mesin|mechanical eng/i],["Teknik Elektro",/teknik elektro|electrical eng|tenaga listrik/i],
    ["Teknik Sipil",/teknik sipil|civil eng/i],["Teknik Industri",/teknik industri|industrial eng/i],
    ["Teknik Kimia",/teknik kimia|chemical eng/i],["Teknik Mekatronika",/mekatronika|mechatronic/i],
    ["Teknik Lingkungan",/teknik lingkungan|environmental eng/i],["Teknik Pertambangan",/pertambangan|mining eng/i],
    ["Teknik Kelautan",/kelautan|ocean|offshore|marine eng/i],["Teknik Metalurgi",/metalurgi|metallurg/i],
    ["Geologi",/geologi|geolog/i],["Arsitektur",/arsitektur|architect/i],
    ["Informatika / Ilmu Komputer",/informatika|ilmu komputer|computer science|teknik komputer/i],
    ["Sistem Informasi",/sistem informasi|information system/i],["Statistika / Matematika",/statistik|matematika|mathemat/i],
    ["Fisika",/fisika|physics/i],["Kimia",/(?<!teknik )kimia|\bchemistry/i],
    ["Akuntansi",/akuntansi|accounting/i],["Manajemen",/\bmanajemen\b(?! (informasi|mutu|risiko))|\bmanagement\b(?! trainee)/i],
    ["Ekonomi",/ekonomi|economics/i],["Keuangan / Perbankan",/keuangan|finance|perbankan/i],
    ["Administrasi Bisnis",/administrasi bisnis|business admin/i],["Hukum",/\bhukum\b|\blaw\b/i],
    ["Psikologi",/psikologi|psycholog/i],["Ilmu Komunikasi",/ilmu komunikasi|jurnalistik|hubungan masyarakat|public relations/i],
    ["DKV / Desain",/\bdkv\b|desain komunikasi visual|desain grafis|graphic design/i],
    ["Kesehatan Masyarakat",/kesehatan masyarakat|kesmas|public health/i],["Gizi",/\bgizi\b|nutrition/i],
    ["Kesehatan Lingkungan",/kesling|kesehatan lingkungan/i],["Farmasi",/farmasi|apoteker|pharma/i],
    ["Kedokteran",/pendidikan dokter|kedokteran(?! (hewan|gigi))|dokter umum/i],["Kedokteran Gigi",/kedokteran gigi|dokter gigi/i],
    ["Keperawatan",/keperawatan|\bners\b|\bperawat\b/i],["Kebidanan",/kebidanan|\bbidan\b/i],
    ["Peternakan",/peternakan|animal husbandry/i],["Kedokteran Hewan",/kedokteran hewan|dokter hewan|veteriner|veterinary/i],
    ["Pertanian / Agribisnis",/pertanian|agribisnis|agronomi|agroteknologi/i],["Teknologi Pangan",/teknologi pangan|food science|ilmu pangan/i],
    ["Kearsipan",/kearsipan/i],
    ["Teknik (semua jurusan teknik)",/\bteknik\b(?!\s+(mesin|elektro|sipil|industri|kimia|lingkungan|pertambangan|kelautan|metalurgi|komputer|informatika|mekatronika|fisika|geologi|ocean|offshore|marine))/i]
  ];
  const ANY_ENG="Teknik (semua jurusan teknik)";
  const _majCache=new WeakMap();
  function majorInfo(j){
    if(_majCache.has(j)) return _majCache.get(j);
    let all=false; const set=new Set();
    if(j.majors){
      const raw=Array.isArray(j.majors)?j.majors:String(j.majors).split(/[,;\n]+/);
      raw.map(s=>String(s).trim()).filter(Boolean).forEach(s=>{ if(ALL_RE.test(s)||s.toLowerCase()===ALL_LABEL.toLowerCase()) all=true; else set.add(s); });
    } else {
      const lines=String(j.requirements||"").split(/\n+/);
      if(ALL_RE.test(String(j.requirements||""))||ALL_RE.test(String(j.title||""))) all=true;
      lines.filter(l=>EDU_LINE.test(l)).forEach(l=>MAJORS.forEach(([lab,re])=>{ if(re.test(l)) set.add(lab); }));
    }
    const info={all,list:[...set].sort((a,b)=>a.localeCompare(b,"id"))};
    _majCache.set(j,info); return info;
  }
  function initials(name){ const w=String(name||"?").replace(/\(.*?\)/g,"").replace(/\b(PT|Tbk|Persero|CV)\b\.?/gi,"").trim().split(/\s+/).filter(Boolean); return ((w[0]||"?")[0]+((w[1]||"")[0]||"")).toUpperCase(); }
  function avatar(name){ let h=0; for(const c of String(name||"")) h=(h*31+c.charCodeAt(0))>>>0; const n=h%6+1; const a=el("span","avatar",initials(name)); a.style.background="var(--av"+n+")"; a.style.color="var(--av"+n+"i)"; a.setAttribute("aria-hidden","true"); return a; }
  function postedText(j){ const src=j.posted||String(j.approved_at||j.found_at||"").slice(0,10); const n=daysLeft(src); if(n===null) return ""; const ago=-n; if(ago<=0) return "Baru dipasang"; if(ago<=30) return "Dipasang "+ago+" hari lalu"; return "Dipasang "+fmtDate(src); }

  const MODES=["On-site","Hybrid","Remote"];
  function workMode(j){
    const wm=String(j.work_mode||"").trim().toLowerCase();
    if(wm==="remote") return "Remote"; if(wm==="hybrid") return "Hybrid"; if(["on-site","onsite","on site","wfo"].includes(wm)) return "On-site";
    const t=[j.employment_type,j.title,j.location,j.province,j.summary].join(" ").toLowerCase();
    if(/hybrid/.test(t)) return "Hybrid";
    if(/\bremote\b|\bwfh\b|work from home|kerja dari rumah|jarak jauh/.test(t)) return "Remote";
    return "On-site";
  }
  const S={open:null};
  let lastFocus=null;

  function card(job){
    const c=el("a","card"); c.href=BASE+"lowongan/"+encodeURIComponent(job.id)+"/";
    const top=el("div","c-top");
    const head=el("div","c-head");
    head.append(el("h2","c-title",job.title||"(tanpa judul)"),el("div","c-company",job.company||""));
    top.append(avatar(job.company),head);
    c.append(top);
    const meta=el("div","c-meta");
    const loc=job.location&&job.location!==job.province?job.location:(job.province||job.location);
    if(loc) meta.append(iconSpan("pin",loc));
    const dg=degs(job); if(dg.length) meta.append(iconSpan("cap",dg.join(" / ")));
    meta.append(iconSpan("home",workMode(job)));
    if(job.employment_type) meta.append(iconSpan("bag",job.employment_type));
    c.append(meta);
    const foot=el("div","c-foot");
    const tags=el("div","tags");
    if(job.field) tags.append(el("span","tag tag-field",job.field));
    if(majorInfo(job).all) tags.append(el("span","tag tag-deg",ALL_LABEL));
    tags.append(deadlinePill(job));
    foot.append(tags);
    const p=postedText(job); if(p) foot.append(el("span","posted",p));
    c.append(foot);
    c.addEventListener("click",e=>{
      if(e.button!==0||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey) return; // let new-tab clicks through
      e.preventDefault(); lastFocus=c; S.open=job.id; renderSheet();
    });
    return c;
  }

  function renderSheet(){
    const sheet=$("#sheet"), scrim=$("#scrim");
    const job=S.open?JOBS.find(x=>x.id===S.open):null;
    if(!job){ if(!sheet.hidden){ sheet.hidden=true; scrim.hidden=true; document.body.classList.remove("locked"); if(lastFocus&&document.contains(lastFocus)) lastFocus.focus(); } S.open=null; return; }
    sheet.textContent="";
    const head=el("div","s-head");
    const h=el("div","c-head");
    const t=el("h2","c-title",job.title||"(tanpa judul)"); t.id="sheetTitle";
    h.append(t,el("div","c-company",job.company||""));
    const close=el("button","close"); close.type="button"; close.innerHTML=ICON.x; close.setAttribute("aria-label","Tutup"); close.onclick=closeSheet;
    head.append(avatar(job.company),h,close);
    const body=el("div","s-body");
    const dl=el("dl","facts");
    const dg=degs(job);
    const facts=[["Lokasi",[job.location,job.province].filter((v,i,a)=>v&&a.indexOf(v)===i).join(", ")],["Jenjang",dg.length?dg.join(" / "):job.degree],["Jurusan",(()=>{ const mi=majorInfo(job); return mi.all?ALL_LABEL:mi.list.join(", "); })()],["Bidang",job.field],["Sistem kerja",workMode(job)],["Tipe kerja",job.employment_type],["Batas lamaran",job.deadline?fmtDate(job.deadline):"Tidak disebut"],["Dipasang",fmtDate(job.posted)]];
    facts.forEach(([k,v])=>{ if(!v) return; const w=el("div"); w.append(el("dt",null,k),el("dd",null,v)); dl.append(w); });
    body.append(dl);
    if(job.summary){ const s=el("section"); s.append(el("h3",null,"Tentang lowongan"),el("p",null,job.summary)); body.append(s); }
    const reqs=String(job.requirements||"").split(/\n+/).map(s=>s.replace(/^[-•*\s]+/,"").trim()).filter(Boolean);
    if(reqs.length){ const s=el("section"); s.append(el("h3",null,"Kualifikasi")); const ul=el("ul","reqs"); reqs.forEach(r=>ul.append(el("li",null,r))); s.append(ul); body.append(s); }
    const act=el("div","s-foot");
    const url=safeUrl(job.apply_url);
    if(url){ const a=el("a","btn btn-primary","Lamar di situs perusahaan ↗"); a.href=url; a.target="_blank"; a.rel="nofollow noopener"; act.append(a); }
    const page=el("a","btn btn-ghost","Halaman lowongan"); page.href=BASE+"lowongan/"+encodeURIComponent(job.id)+"/"; act.append(page);
    act.append(el("p","warn-note","Lowongan resmi tidak memungut biaya apa pun."));
    sheet.append(head,body,act);
    sheet.hidden=false; scrim.hidden=false; document.body.classList.add("locked"); close.focus();
  }
  function closeSheet(){ S.open=null; renderSheet(); }
  $("#scrim").onclick=closeSheet;
  document.addEventListener("keydown",e=>{ if(e.key==="Escape"&&S.open) closeSheet(); });

  function empty(title,sub){ const e=el("div","empty"); e.append(el("strong",null,title),document.createTextNode(sub)); return e; }
  function fillSelect(sel,values,label){
    const cur=sel.value; sel.textContent="";
    const o=el("option",null,label); o.value=""; sel.append(o);
    values.forEach(v=>{ const op=el("option",null,v); op.value=v; sel.append(op); });
    if(values.includes(cur)) sel.value=cur;
  }
  function render(){
    const live=JOBS.filter(j=>!(daysLeft(j.deadline)<0));
    const provs=[...new Set(live.map(j=>j.province).filter(Boolean))].sort();
    const fields=[...new Set(live.map(j=>j.field).filter(Boolean))].sort();
    const found=new Set(live.flatMap(degs));
    const degOpts=DEG_ORDER.filter(k=>DEG_BASE.includes(k)||found.has(k));
    fillSelect($("#prov"),provs,"Semua provinsi");
    fillSelect($("#deg"),degOpts,"Semua jenjang");
    const majSel=$("#maj"), majCur=majSel.value;
    const majList=[...new Set(live.flatMap(j=>majorInfo(j).list))].sort((a,b)=>a.localeCompare(b,"id"));
    majSel.textContent="";
    [["","Pilih jurusan"],[ALL_VAL,ALL_LABEL],...majList.map(m=>[m,m])].forEach(([v,l])=>{ const o=el("option",null,l); o.value=v; majSel.append(o); });
    if(majCur===ALL_VAL||majList.includes(majCur)) majSel.value=majCur;
    fillSelect($("#field"),fields,"Semua bidang");
    const modeSel=$("#mode"), modeCur=modeSel.value; modeSel.textContent="";
    [["","Semua sistem kerja"],...MODES.map(x=>[x,x+" ("+live.filter(j=>workMode(j)===x).length+")"])].forEach(([v,l])=>{ const o=el("option",null,l); o.value=v; modeSel.append(o); });
    modeSel.value=modeCur;
    const q=$("#q").value.trim().toLowerCase(), p=$("#prov").value, g=$("#deg").value, m=majSel.value, f=$("#field").value, w=$("#mode").value;
    const majOk=j=>{ if(!m) return true; const mi=majorInfo(j); return m===ALL_VAL?mi.all:(mi.all||mi.list.includes(m)||(m.startsWith("Teknik ")&&mi.list.includes(ANY_ENG))); };
    const shown=live.filter(j=>(!p||j.province===p)&&(!f||j.field===f)&&(!w||workMode(j)===w)&&(!g||degs(j).includes(g))&&majOk(j)&&(!q||[j.title,j.company,j.location,j.province,j.field].join(" ").toLowerCase().includes(q)))
      .sort((a,b)=>String(b.approved_at||"").localeCompare(String(a.approved_at||"")));
    const list=$("#jobList"); list.textContent="";
    if(!live.length) list.append(empty("Belum ada lowongan aktif","Lowongan baru ditambahkan setiap hari. Kunjungi lagi besok."));
    else if(!shown.length) list.append(empty("Tidak ada yang cocok","Coba kata kunci lain atau hapus filter."));
    else shown.forEach(j=>list.append(card(j)));
    const cnt=$("#count"); if(cnt) cnt.textContent=live.length;
    const sh=$("#shown"); if(sh){ sh.textContent=""; const b=el("strong",null,String(shown.length)); sh.append(b,document.createTextNode(shown.length===live.length?" lowongan aktif":" dari "+live.length+" lowongan aktif")); }
  }

  ["#q","#prov","#field","#deg","#maj","#mode"].forEach(s=>$(s).addEventListener("input",()=>render()));
  render();
})();
