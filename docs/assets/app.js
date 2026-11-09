// Esokerja: filter the job list and keep deadline badges current in the reader's own date.
(function () {
  var MONTHS = ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agu","Sep","Okt","Nov","Des"];
  function today() {
    // Date in Indonesia's western time (UTC+7), where most deadlines are set.
    var d = new Date(Date.now() + 7 * 3600e3);
    return Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate());
  }
  function daysLeft(iso) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(iso || "")) return null;
    var p = iso.split("-");
    return Math.round((Date.UTC(+p[0], +p[1] - 1, +p[2]) - today()) / 864e5);
  }
  function fmt(iso) { var p = iso.split("-"); return (+p[2]) + " " + MONTHS[+p[1] - 1] + " " + p[0]; }

  function badge(el) {
    var iso = el.getAttribute("data-deadline");
    var n = daysLeft(iso);
    if (n === null) { el.className = "date"; el.textContent = "Batas tidak dicantumkan"; return n; }
    if (n < 0) { el.className = "pill p-closed"; el.textContent = "Ditutup"; }
    else if (n <= 7) { el.className = "pill p-soon"; el.textContent = n === 0 ? "Tutup hari ini" : n + " hari lagi"; }
    else { el.className = "date"; el.textContent = "s.d. " + fmt(iso); }
    return n;
  }

  // Detail page: deadline badge + closed banner
  document.querySelectorAll("span[data-deadline]").forEach(function (el) {
    var n = badge(el);
    var banner = document.getElementById("closed");
    if (banner && el.hasAttribute("data-main") && n !== null && n < 0) banner.hidden = false;
  });

  var list = document.getElementById("jobs");
  if (!list) return;
  var rows = Array.prototype.slice.call(list.querySelectorAll(".job"));
  rows.forEach(function (r) {
    var n = daysLeft(r.getAttribute("data-deadline"));
    r.dataset.closed = n !== null && n < 0 ? "1" : "";
  });
  var q = document.getElementById("q"), prov = document.getElementById("prov"), field = document.getElementById("field");
  var empty = document.getElementById("empty"), count = document.getElementById("count");

  function apply() {
    var s = (q.value || "").trim().toLowerCase(), p = prov.value, f = field.value, shown = 0, open = 0;
    rows.forEach(function (r) {
      var ok = !r.dataset.closed &&
        (!p || r.getAttribute("data-prov") === p) &&
        (!f || r.getAttribute("data-field") === f) &&
        (!s || r.getAttribute("data-text").indexOf(s) !== -1);
      r.hidden = !ok;
      if (ok) shown++;
      if (!r.dataset.closed) open++;
    });
    empty.hidden = shown !== 0;
    if (count) count.textContent = open;
  }
  [q, prov, field].forEach(function (el) { el.addEventListener("input", apply); });

  // Remember last filters in the URL hash-free query so links can be shared.
  try {
    var u = new URL(location.href);
    if (u.searchParams.get("q")) q.value = u.searchParams.get("q");
    if (u.searchParams.get("provinsi")) prov.value = u.searchParams.get("provinsi");
    if (u.searchParams.get("bidang")) field.value = u.searchParams.get("bidang");
  } catch (e) {}
  apply();
})();
