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
import shutil

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "docs"
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
BASE_URL = CFG["base_url"].rstrip("/")
BASE = CFG["base_path"] if CFG["base_path"].endswith("/") else CFG["base_path"] + "/"
SITE = CFG["site_name"]
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


LOGO = ('<svg width="26" height="26" viewBox="0 0 26 26" aria-hidden="true">'
        '<path d="M4 18a9 9 0 0 1 18 0Z" fill="var(--sun)"/>'
        '<path d="M2 21h22" stroke="var(--ink)" stroke-width="2.4" stroke-linecap="round"/>'
        '<path d="M13 4v3M5.6 7.6l2 2M20.4 7.6l-2 2" stroke="var(--sun)" stroke-width="2.2" stroke-linecap="round"/></svg>')

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700;12..96,800'
         '&family=IBM+Plex+Mono:wght@400;500&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap">')


def page(title, description, path, body, current="", extra_head="", noindex=False):
    canonical = BASE_URL + "/" + path
    full_title = title if title == SITE else f"{title} | {SITE}"
    cur = ' aria-current="page"'
    nav = "".join(
        f'<a href="{BASE}{href}"{cur if key == current else ""}>{label}</a>'
        for key, href, label in [("home", "", "Lowongan"), ("about", "tentang/", "Tentang")]
    )
    robots = '<meta name="robots" content="noindex">' if noindex else ""
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
<meta name="theme-color" content="#16223B">
<link rel="icon" href="{BASE}assets/icon.svg" type="image/svg+xml">
{robots}{FONTS}
<link rel="stylesheet" href="{BASE}assets/style.css">
{extra_head}
</head>
<body>
<header class="top"><div class="wrap">
<a class="logo" href="{BASE}">{LOGO}<span><b>esok</b>erja</span></a>
<nav class="nav" aria-label="Utama">{nav}</nav>
</div></header>
<main>
{body}
</main>
<footer><div class="wrap">
<span>© {TODAY.year} {e(SITE)}. Info lowongan dari sumber resmi perusahaan dan instansi.</span>
<nav aria-label="Kaki halaman"><a href="{BASE}tentang/">Tentang</a><a href="{BASE}privasi/">Kebijakan Privasi</a></nav>
</div></footer>
<script src="{BASE}assets/app.js" defer></script>
</body>
</html>
"""


NOTICE = ('<p class="notice" role="note"><span aria-hidden="true">!</span><span><strong>Lowongan resmi tidak memungut biaya.</strong> '
          'Jika diminta transfer uang untuk tes, pelatihan, seragam, atau tiket, itu penipuan.</span></p>')


def deadline_badge(job, main=False):
    d = parse_date(job.get("deadline"))
    n = days_left(job)
    attr = f' data-deadline="{e(job.get("deadline", ""))}"' + (" data-main" if main else "")
    if n is None:
        return f'<span class="date"{attr}>Batas tidak dicantumkan</span>'
    if n < 0:
        return f'<span class="pill p-closed"{attr}>Ditutup</span>'
    if n <= 7:
        return f'<span class="pill p-soon"{attr}>{"Tutup hari ini" if n == 0 else f"{n} hari lagi"}</span>'
    return f'<span class="date"{attr}>s.d. {fmt(d)}</span>'


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
    place = ", ".join(x for x in [job.get("location"), job.get("province")] if x)
    summary = lines(job.get("summary"))
    reqs = lines(job.get("requirements"))
    facts = [
        ("Lokasi", place), ("Bidang", job.get("field")), ("Pendidikan", job.get("degree")),
        ("Tipe", job.get("employment_type")),
        ("Batas lamaran", fmt(parse_date(job.get("deadline")), True) or "Tidak dicantumkan"),
        ("Dipasang", fmt(parse_date(job.get("posted")), True)),
    ]
    facts_html = "".join(f"<div><dt>{k}</dt><dd>{e(v)}</dd></div>" for k, v in facts if v)
    url = safe_url(job.get("apply_url"))
    apply = ""
    if url:
        apply = (f'<div class="apply"><a class="btn" href="{e(url)}" target="_blank" rel="nofollow noopener">Lamar di situs resmi ↗</a>'
                 f'<span class="hint">Kamu akan diarahkan ke halaman pendaftaran {e(company) or "perusahaan"}.</span></div>')
    body = f"""<div class="wrap">
<p class="crumb"><a href="{BASE}">← Semua lowongan</a></p>
<article class="detail">
<h1>{e(title)}</h1>
<p class="company">{e(company)} <span>· {e(place)}</span></p>
<p style="margin:10px 0 0">{deadline_badge(job, main=True)}</p>
<p class="closed-banner" id="closed"{"" if closed else " hidden"}>Pendaftaran lowongan ini sudah ditutup.</p>
<dl class="facts">{facts_html}</dl>
<div class="body">
{"<h2>Tentang lowongan</h2>" + "".join(f"<p>{e(p)}</p>" for p in summary) if summary else ""}
{"<h2>Persyaratan</h2><ul>" + "".join(f"<li>{e(r)}</li>" for r in reqs) + "</ul>" if reqs else ""}
</div>
{apply}
<p class="hint" style="margin-top:18px">Detail dapat berubah sewaktu-waktu. Pastikan informasi terbaru di situs resmi sebelum melamar.</p>
</article>
{NOTICE}
</div>"""
    desc = f"Lowongan {title} di {company}, {place}. " + (summary[0] if summary else "")
    desc = desc[:155].rsplit(" ", 1)[0] + "…" if len(desc) > 160 else desc
    return page(f"{title} – {company}", desc, f"lowongan/{job['id']}/", body,
                extra_head="" if closed else job_posting_ld(job), noindex=closed)


def index_page(jobs):
    open_jobs = [j for j in jobs if not ((days_left(j) or 0) < 0)]
    provs = sorted({j.get("province") for j in open_jobs if j.get("province")})
    fields = sorted({j.get("field") for j in open_jobs if j.get("field")})
    opt = lambda vals, label: f'<option value="">{label}</option>' + "".join(f'<option value="{e(v)}">{e(v)}</option>' for v in vals)
    rows = []
    for j in jobs:
        text = " ".join(str(j.get(k, "")) for k in ("title", "company", "location", "province", "field")).lower()
        place = j.get("location") or j.get("province") or ""
        field_pill = f'<span class="pill p-field">{e(j.get("field"))}</span>' if j.get("field") else ""
        rows.append(
            f'<li class="job" data-prov="{e(j.get("province"))}" data-field="{e(j.get("field"))}" '
            f'data-deadline="{e(j.get("deadline"))}" data-text="{e(text)}"{" hidden" if (days_left(j) or 0) < 0 else ""}>'
            f'<a href="{BASE}lowongan/{e(j["id"])}/">'
            f'<span class="j-title">{e(j.get("title"))}</span>'
            f'<span class="j-meta">{e(j.get("company"))} · {e(place)}</span>'
            f'<span class="j-side">{field_pill}{deadline_badge(j)}</span>'
            f"</a></li>"
        )
    body = f"""<section class="hero"><div class="wrap">
<h1>Lowongan S-1 untuk <em>hari esokmu</em>.</h1>
<p class="lede">Info lowongan kerja lulusan sarjana dari seluruh Indonesia. Setiap lowongan dicek manual sebelum tayang, dan pendaftarannya langsung di situs resmi perusahaan.</p>
<p class="stats"><strong id="count">{len(open_jobs)}</strong> lowongan aktif · {len(provs)} provinsi · diperbarui {fmt(TODAY, True)}</p>
</div></section>
<div class="wrap">
{NOTICE}
<div class="filters" role="search">
<input class="q" id="q" type="search" placeholder="Cari posisi atau perusahaan" aria-label="Cari posisi atau perusahaan">
<select id="prov" aria-label="Provinsi">{opt(provs, "Semua provinsi")}</select>
<select id="field" aria-label="Bidang">{opt(fields, "Semua bidang")}</select>
</div>
<ul class="list" id="jobs">{"".join(rows)}</ul>
<div class="empty" id="empty"{"" if not open_jobs else " hidden"}><strong>Tidak ada lowongan yang cocok</strong>Coba kata kunci lain atau hapus filter.</div>
</div>"""
    return page(SITE, "Info lowongan kerja S-1 terbaru di seluruh Indonesia: BUMN, bank, instansi, dan swasta. Dicek manual, daftar langsung di situs resmi.",
                "", body, current="home")


def about_page():
    contact = CFG.get("contact_email", "").strip()
    contact_html = (f"<p>Untuk koreksi informasi atau pemasangan lowongan, hubungi kami di <strong>{e(contact)}</strong>.</p>"
                    if contact else "<p>Untuk koreksi informasi atau pemasangan lowongan, hubungi pengelola situs ini.</p>")
    body = f"""<div class="wrap prose">
<h1>Tentang {e(SITE)}</h1>
<p>{e(SITE)} mengumpulkan info lowongan kerja untuk lulusan S-1 dari seluruh Indonesia. Namanya gabungan dari <em>esok</em> dan <em>kerja</em>: pekerjaan untuk hari esok.</p>
<h2>Cara kami memilih lowongan</h2>
<ul>
<li>Lowongan dicari dari halaman karier resmi perusahaan, portal rekrutmen instansi, dan pengumuman resmi lainnya.</li>
<li>Setiap lowongan dicek manual sebelum tayang: link pendaftaran harus mengarah ke kanal resmi, dan tidak ada pungutan biaya.</li>
<li>Lowongan yang batas pendaftarannya sudah lewat otomatis ditandai ditutup dan diturunkan.</li>
</ul>
<h2>Kami tidak menerima lamaran</h2>
<p>{e(SITE)} hanya menyebarkan informasi. Semua pendaftaran dilakukan langsung di situs resmi perusahaan. Kami tidak meminta data pribadi, CV, atau biaya apa pun dari pelamar.</p>
<h2>Kontak</h2>
{contact_html}
</div>"""
    return page("Tentang", f"Tentang {SITE}: info lowongan S-1 seluruh Indonesia yang dicek manual.", "tentang/", body, current="about")


def privacy_page():
    body = f"""<div class="wrap prose">
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
    body = f"""<div class="wrap prose"><h1>Halaman tidak ditemukan</h1>
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
    write("assets/icon.svg", LOGO.replace('aria-hidden="true"', 'xmlns="http://www.w3.org/2000/svg"')
          .replace("var(--sun)", "#C4520F").replace("var(--ink)", "#16223B"))

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
