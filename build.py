#!/usr/bin/env python3
"""Build the Esokerja static site from data/jobs.json into docs/ (served by GitHub Pages).

Usage: python3 build.py
Only the Python standard library is used.
"""
import datetime as dt
import html
import json
import pathlib
import re
import hashlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "docs"
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
BASE_URL = CFG["base_url"].rstrip("/")
BASE = CFG["base_path"] if CFG["base_path"].endswith("/") else CFG["base_path"] + "/"
SITE = CFG["site_name"]
VER = lambda name: hashlib.sha1((ROOT / "src" / name).read_bytes()).hexdigest()[:8]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
MONTHS_LONG = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus",
               "September", "Oktober", "November", "Desember"]
TODAY = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=CFG.get("timezone_offset_hours", 7))).date()
KEEP_CLOSED_DAYS = 30  # closed jobs keep a page (marked closed) this long, then drop out

e = lambda s: html.escape(str(s or ""), quote=True)


def parse_date(s):
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def fmt(d, long=False):
    if not d:
        return ""
    return f"{d.day} {(MONTHS_LONG if long else MONTHS)[d.month - 1]} {d.year}"


def days_left(job):
    d = parse_date(job.get("deadline"))
    return None if d is None else (d - TODAY).days


def lines(text):
    return [re.sub(r"^[-•*\s]+", "", x).strip() for x in str(text or "").splitlines() if x.strip()]


def safe_url(u):
    return u if isinstance(u, str) and re.match(r"^https?://", u) else ""


LOGO_MARK = ('<svg width="22" height="22" viewBox="0 0 26 26" aria-hidden="true">'
             '<path d="M4.5 18a8.5 8.5 0 0 1 17 0Z" fill="#0F2547"/>'
             '<path d="M2.5 21.5h21" stroke="#0F2547" stroke-width="2.6" stroke-linecap="round"/>'
             '<path d="M13 3.5v3M5.8 7l2 2M20.2 7l-2 2" stroke="#0F2547" stroke-width="2.4" stroke-linecap="round"/></svg>')
ICON_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 34 34">'
            '<rect width="34" height="34" rx="9" fill="#FFC83D"/><g transform="translate(4 4)">'
            '<path d="M4.5 18a8.5 8.5 0 0 1 17 0Z" fill="#0F2547"/>'
            '<path d="M2.5 21.5h21" stroke="#0F2547" stroke-width="2.6" stroke-linecap="round"/>'
            '<path d="M13 3.5v3M5.8 7l2 2M20.2 7l-2 2" stroke="#0F2547" stroke-width="2.4" stroke-linecap="round"/></g></svg>')

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap">')

SVG = {
    "search": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
    "pin": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21Z"/><circle cx="12" cy="9.5" r="2.5"/></svg>',
    "cap": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m2 9 10-5 10 5-10 5L2 9Z"/><path d="M6 11v5c3 2.5 9 2.5 12 0v-5"/></svg>',
    "book": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M4 5a2 2 0 0 1 2-2h12v16H6a2 2 0 0 0-2 2V5Z"/><path d="M4 19a2 2 0 0 1 2-2h12"/></svg>',
}


def page(title, description, path, body, current="", extra_head="", noindex=False, band_extra=""):
    canonical = BASE_URL + "/" + path
    full_title = title if title == SITE else f"{title} | {SITE}"
    cur = ' aria-current="page"'
    nav = "".join(
        f'<a href="{BASE}{href}"{cur if key == current else ""}>{label}</a>'
        for key, href, label in [("home", "", "Lowongan"), ("about", "tentang/", "Tentang")]
    )
    robots = '<meta name="robots" content="noindex">' if noindex else ""
    band_cls = "band" if band_extra else "band slim"
    return f"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(full_title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{e(canonical)}">
<meta property="og:site_name" content="{e(SITE)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="id_ID">
<meta name="theme-color" content="#0F2547">
<link rel="icon" href="{BASE}assets/icon.svg" type="image/svg+xml">
{robots}{FONTS}
<link rel="stylesheet" href="{BASE}assets/style.css?v={VER('style.css')}">
{extra_head}
</head>
<body data-base="{e(BASE)}">
<header class="{band_cls}"><div class="wrap">
<div class="topbar">
<a class="logo" href="{BASE}"><span class="logo-mark">{LOGO_MARK}</span>{e(SITE)}</a>
<nav class="nav" aria-label="Utama">{nav}</nav>
</div>
{band_extra}
</div></header>
<main class="wrap">
{body}
</main>
<footer><div class="wrap">
<span>{e(SITE)} mengumpulkan info dari halaman karier resmi. Selalu pastikan detail di situs perusahaan sebelum melamar.</span>
<nav aria-label="Kaki halaman"><a href="{BASE}tentang/">Tentang</a><a href="{BASE}privasi/">Kebijakan Privasi</a></nav>
</div></footer>
<script src="{BASE}assets/app.js?v={VER('app.js')}" defer></script>
</body>
</html>
"""


DEG_ORDER = ["SMA", "SMK", "D3", "D4", "S1", "S2", "S3"]


def degs(job):
    s = re.sub(r"([SD])-(\d)", r"\1\2", str(job.get("degree", "")).upper())
    return [k for k in DEG_ORDER if re.search(r"(^|[^A-Z0-9])" + k + r"([^A-Z0-9]|$)", s)]


def initials(name):
    s = re.sub(r"\(.*?\)", "", str(name or "?"))
    s = re.sub(r"\b(PT|Tbk|Persero|CV)\b\.?", "", s, flags=re.I).strip()
    w = [x for x in s.split() if x]
    return (((w[0] if w else "?")[0]) + ((w[1][0]) if len(w) > 1 else "")).upper()


def avatar_html(name):
    h = 0
    for ch in str(name or ""):
        cp = ord(ch)
        unit = cp if cp < 0x10000 else 0xD800 + ((cp - 0x10000) >> 10)
        h = (h * 31 + unit) & 0xFFFFFFFF
    n = h % 6 + 1
    return f'<span class="avatar" aria-hidden="true" style="background:var(--av{n});color:var(--av{n}i)">{e(initials(name))}</span>'


def deadline_pill(job):
    d = parse_date(job.get("deadline"))
    n = days_left(job)
    if n is None:
        return '<span class="pill p-none" id="deadlinePill">Batas tidak disebut</span>'
    if n < 0:
        return '<span class="pill p-exp" id="deadlinePill">Ditutup</span>'
    if n <= 7:
        return f'<span class="pill p-soon" id="deadlinePill">{"Tutup hari ini" if n == 0 else f"Tutup {n} hari lagi"}</span>'
    return f'<span class="pill p-open" id="deadlinePill">s.d. {fmt(d)}</span>'


def employment_enum(text):
    t = str(text or "").lower()
    if "magang" in t or "intern" in t:
        return "INTERN"
    if "paruh" in t or "part" in t:
        return "PART_TIME"
    if "kontrak" in t or "contract" in t:
        return "CONTRACTOR"
    if "sementara" in t or "temporary" in t:
        return "TEMPORARY"
    return "FULL_TIME"


def job_posting_ld(job):
    posted = parse_date(job.get("posted")) or parse_date(job.get("approved_at")) or TODAY
    desc = "".join(f"<p>{e(p)}</p>" for p in lines(job.get("summary")))
    reqs = lines(job.get("requirements"))
    if reqs:
        desc += "<p>Persyaratan:</p><ul>" + "".join(f"<li>{e(r)}</li>" for r in reqs) + "</ul>"
    ld = {
        "@context": "https://schema.org/",
        "@type": "JobPosting",
        "title": job.get("title", ""),
        "description": desc or e(job.get("title", "")),
        "identifier": {"@type": "PropertyValue", "name": SITE, "value": job["id"]},
        "datePosted": posted.isoformat(),
        "employmentType": employment_enum(job.get("employment_type")),
        "hiringOrganization": {"@type": "Organization", "name": job.get("company", "")},
        "directApply": False,
        "educationRequirements": {"@type": "EducationalOccupationalCredential", "credentialCategory": "bachelor degree"},
    }
    d = parse_date(job.get("deadline"))
    if d:
        ld["validThrough"] = f"{d.isoformat()}T23:59:00+07:00"
    prov = str(job.get("province", "")).strip()
    city = str(job.get("location", "")).split(",")[0].strip()
    if prov.lower() == "remote":
        ld["jobLocationType"] = "TELECOMMUTE"
        ld["applicantLocationRequirements"] = {"@type": "Country", "name": "Indonesia"}
    else:
        addr = {"@type": "PostalAddress", "addressCountry": "ID"}
        if prov and prov.lower() != "seluruh indonesia":
            addr["addressRegion"] = prov
        if city and not city.lower().startswith(("berbagai", "seluruh")):
            addr["addressLocality"] = city
        ld["jobLocation"] = {"@type": "Place", "address": addr}
    return '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>"


def job_page(job):
    n = days_left(job)
    closed = n is not None and n < 0
    title = job.get("title", "Lowongan")
    company = job.get("company", "")
    place = ", ".join(dict.fromkeys(x for x in [job.get("location"), job.get("province")] if x))
    summary = lines(job.get("summary"))
    reqs = lines(job.get("requirements"))
    dg = degs(job)
    majors = job.get("majors")
    if isinstance(majors, list):
        majors = ", ".join(majors)
    facts = [
        ("Lokasi", place), ("Jenjang", " / ".join(dg) if dg else job.get("degree")), ("Jurusan", majors),
        ("Bidang", job.get("field")), ("Tipe kerja", job.get("employment_type")),
        ("Batas lamaran", fmt(parse_date(job.get("deadline"))) or "Tidak disebut"),
        ("Dipasang", fmt(parse_date(job.get("posted")))),
    ]
    facts_html = "".join(f"<div><dt>{k}</dt><dd>{e(v)}</dd></div>" for k, v in facts if v)
    url = safe_url(job.get("apply_url"))
    apply = (f'<a class="btn btn-primary" href="{e(url)}" target="_blank" rel="nofollow noopener">Lamar di situs perusahaan ↗</a>' if url else "")
    sections = ""
    if summary:
        sections += "<section><h3>Tentang lowongan</h3>" + "".join(f"<p>{e(p)}</p>" for p in summary) + "</section>"
    if reqs:
        sections += '<section><h3>Kualifikasi</h3><ul class="reqs">' + "".join(f"<li>{e(r)}</li>" for r in reqs) + "</ul></section>"
    body = f"""<p class="crumb"><a href="{BASE}">← Semua lowongan</a></p>
<article class="panel" data-job-deadline="{e(job.get("deadline", ""))}">
<div class="s-head">{avatar_html(company)}<div class="c-head"><h1 class="c-title">{e(title)}</h1><div class="c-company">{e(company)}</div>
<div style="margin-top:8px">{deadline_pill(job)}</div></div></div>
<div class="s-body">
<p class="closed-banner" id="closed"{"" if closed else " hidden"}>Pendaftaran lowongan ini sudah ditutup.</p>
<dl class="facts">{facts_html}</dl>
{sections}
<p class="hint" style="margin:0">Detail dapat berubah sewaktu-waktu. Pastikan informasi terbaru di situs resmi sebelum melamar.</p>
</div>
<div class="s-foot">{apply}<p class="warn-note">Lowongan resmi tidak memungut biaya apa pun. Jika diminta transfer uang untuk tes, pelatihan, seragam, atau tiket, itu penipuan.</p></div>
</article>"""
    desc = f"Lowongan {title} di {company}, {place}. " + (summary[0] if summary else "")
    desc = desc[:155].rsplit(" ", 1)[0] + "…" if len(desc) > 160 else desc
    return page(f"{title} – {company}", desc, f"lowongan/{job['id']}/", body,
                extra_head="" if closed else job_posting_ld(job), noindex=closed)


def index_page(jobs):
    open_jobs = [j for j in jobs if not ((days_left(j) or 0) < 0)]
    provs = sorted({j.get("province") for j in open_jobs if j.get("province")})
    data = json.dumps(open_jobs, ensure_ascii=False).replace("</", "<\\/")
    links = "".join(f'<li><a href="{BASE}lowongan/{e(j["id"])}/">{e(j.get("title"))} – {e(j.get("company"))}</a></li>' for j in open_jobs)
    band = f"""<div class="intro"><h1>{e(SITE)} mengumpulkan info lowongan kerja dari seluruh Indonesia</h1></div>
<div class="searchbar" id="searchbar" role="search">
<label class="sb-cell">{SVG["search"]}<input id="q" type="search" placeholder="Posisi, perusahaan, atau kata kunci" aria-label="Cari posisi atau perusahaan"></label>
<label class="sb-cell">{SVG["pin"]}<select id="prov" aria-label="Provinsi"><option value="">Semua provinsi</option></select></label>
<label class="sb-cell">{SVG["cap"]}<select id="deg" aria-label="Jenjang pendidikan"><option value="">Semua jenjang</option></select></label>
<label class="sb-cell">{SVG["book"]}<select id="maj" aria-label="Jurusan"><option value="">Pilih jurusan</option></select></label>
</div>"""
    body = f"""<div class="cats" id="cats" role="group" aria-label="Bidang"></div>
<div class="grid" id="jobList"><noscript><div class="noscript-list"><ul>{links}</ul></div></noscript></div>
<script type="application/json" id="jobs-data">{data}</script>
<div class="scrim" id="scrim" hidden></div>
<aside class="sheet" id="sheet" role="dialog" aria-modal="true" aria-labelledby="sheetTitle" hidden></aside>"""
    return page(SITE, "Info lowongan kerja S-1 terbaru di seluruh Indonesia: BUMN, bank, instansi, dan swasta. Dicek manual, daftar langsung di situs resmi.",
                "", body, current="home", band_extra=band)


def about_page():
    contact = CFG.get("contact_email", "").strip()
    contact_html = (f"<p>Untuk koreksi informasi atau pemasangan lowongan, hubungi kami di <strong>{e(contact)}</strong>.</p>"
                    if contact else "<p>Untuk koreksi informasi atau pemasangan lowongan, hubungi pengelola situs ini.</p>")
    body = f"""<div class="prose">
<h1>Tentang {e(SITE)}</h1>
<p>{e(SITE)} mengumpulkan info lowongan kerja untuk lulusan S-1 dari seluruh Indonesia. Namanya gabungan dari <em>esok</em> dan <em>kerja</em>: pekerjaan untuk hari esok.</p>
<h2>Kami tidak menerima lamaran</h2>
<p>{e(SITE)} hanya menyebarkan informasi. Semua pendaftaran dilakukan langsung di situs resmi perusahaan. Kami tidak meminta data pribadi, CV, atau biaya apa pun dari pelamar.</p>
</div>"""
    return page("Tentang", f"Tentang {SITE}: info lowongan S-1 seluruh Indonesia yang dicek manual.", "tentang/", body, current="about")


def privacy_page():
    body = f"""<div class="prose">
<h1>Kebijakan Privasi</h1>
<p>Terakhir diperbarui {fmt(TODAY, True)}.</p>
<h2>Data yang kami kumpulkan</h2>
<p>{e(SITE)} tidak memiliki fitur akun, formulir lamaran, atau unggah CV. Kami tidak mengumpulkan nama, email, atau data pribadi pengunjung secara langsung.</p>
<h2>Layanan pihak ketiga</h2>
<p>Situs ini di-hosting oleh GitHub Pages dan memuat huruf dari Google Fonts. Layanan tersebut dapat mencatat data teknis seperti alamat IP dan jenis browser sesuai kebijakan privasi masing-masing. Jika di kemudian hari kami menampilkan iklan (misalnya Google AdSense) atau memasang analitik, penyedia layanan tersebut dapat menggunakan cookie untuk menampilkan iklan yang relevan. Halaman ini akan diperbarui saat itu terjadi.</p>
<h2>Tautan ke situs lain</h2>
<p>Tombol lamar mengarahkan kamu ke situs resmi perusahaan atau instansi. Data yang kamu berikan di sana tunduk pada kebijakan privasi situs tersebut.</p>
<h2>Perubahan kebijakan</h2>
<p>Kebijakan ini dapat diperbarui sewaktu-waktu. Tanggal pembaruan terakhir tercantum di atas.</p>
</div>"""
    return page("Kebijakan Privasi", f"Kebijakan privasi {SITE}.", "privasi/", body)


def not_found_page():
    body = f"""<div class="prose"><h1>Halaman tidak ditemukan</h1>
<p>Lowongan ini mungkin sudah ditutup dan diturunkan.</p><p><a href="{BASE}">← Lihat lowongan yang masih dibuka</a></p></div>"""
    return page("Halaman tidak ditemukan", "Halaman tidak ditemukan.", "404.html", body, noindex=True)


def write(path, text):
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def main():
    jobs = json.loads((ROOT / "data" / "jobs.json").read_text(encoding="utf-8"))
    # Drop jobs closed for longer than KEEP_CLOSED_DAYS; sort open-first, newest approval first.
    jobs = [j for j in jobs if days_left(j) is None or days_left(j) >= -KEEP_CLOSED_DAYS]
    jobs.sort(key=lambda j: str(j.get("approved_at", "")), reverse=True)
    jobs.sort(key=lambda j: (days_left(j) or 0) < 0)

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    (OUT / ".nojekyll").write_text("")
    (OUT / "assets").mkdir()
    shutil.copy(ROOT / "src" / "style.css", OUT / "assets" / "style.css")
    shutil.copy(ROOT / "src" / "app.js", OUT / "assets" / "app.js")
    write("assets/icon.svg", ICON_SVG)

    write("index.html", index_page(jobs))
    for j in jobs:
        write(f"lowongan/{j['id']}/index.html", job_page(j))
    write("tentang/index.html", about_page())
    write("privasi/index.html", privacy_page())
    write("404.html", not_found_page())

    urls = [("", TODAY), ("tentang/", None), ("privasi/", None)]
    urls += [(f"lowongan/{j['id']}/", parse_date(j.get("approved_at")) or parse_date(j.get("posted")))
             for j in jobs if (days_left(j) or 0) >= 0]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, d in urls:
        sm.append(f"<url><loc>{e(BASE_URL + '/' + path)}</loc>" + (f"<lastmod>{d.isoformat()}</lastmod>" if d else "") + "</url>")
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm) + "\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")
    if CFG.get("custom_domain"):
        write("CNAME", CFG["custom_domain"].strip() + "\n")

    n_open = sum(1 for j in jobs if (days_left(j) or 0) >= 0)
    print(f"Built {len(jobs)} job pages ({n_open} open) into docs/ for {TODAY.isoformat()}")


if __name__ == "__main__":
    main()
