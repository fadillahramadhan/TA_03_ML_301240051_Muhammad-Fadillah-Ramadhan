(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const form = $("#form"), result = $("#result-body"), errBox = $("#errors"), btn = $("#submit");

  /* ---------- tema ---------- */
  const root = document.documentElement;
  const saved = localStorage.getItem("theme");
  if (saved) root.dataset.theme = saved;
  else if (matchMedia("(prefers-color-scheme: dark)").matches) root.dataset.theme = "dark";
  $("#theme").addEventListener("click", () => {
    root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
    localStorage.setItem("theme", root.dataset.theme);
  });

  /* ---------- contoh nasabah ---------- */
  const mk = (o, pay, bill, pamt) => {
    const d = { ...o };
    for (let i = 1; i <= 6; i++) { d["PAY_" + i] = pay[i - 1]; d["BILL_AMT" + i] = bill[i - 1]; d["PAY_AMT" + i] = pamt[i - 1]; }
    return d;
  };
  const PRESETS = {
    aman: mk({ LIMIT_BAL: 200000, AGE: 38, SEX: 2, EDUCATION: 2, MARRIAGE: 1 },
      [0, 0, 0, 0, 0, 0], [62000, 58000, 60000, 61000, 59000, 60000], [62000, 58000, 60000, 61000, 59000, 60000]),
    sedang: mk({ LIMIT_BAL: 80000, AGE: 30, SEX: 2, EDUCATION: 2, MARRIAGE: 2 },
      [0, 0, 0, 0, 0, 0], [50000, 49000, 48000, 47500, 47000, 46000], [2000, 2000, 2000, 2000, 2000, 2000]),
    risiko: mk({ LIMIT_BAL: 30000, AGE: 27, SEX: 2, EDUCATION: 3, MARRIAGE: 2 },
      [3, 3, 3, 3, 3, 3], [29000, 29500, 28800, 28000, 27500, 27000], [0, 0, 0, 0, 0, 0]),
  };
  function fill(d) {
    Object.entries(d).forEach(([k, v]) => {
      if (k === "SEX") { const r = form.querySelector(`input[name=SEX][value="${v}"]`); if (r) r.checked = true; }
      else if (form.elements[k]) form.elements[k].value = v;
    });
    errBox.classList.remove("show");
    form.querySelectorAll(".invalid").forEach(e => e.classList.remove("invalid"));
  }
  document.querySelectorAll("[data-preset]").forEach(b =>
    b.addEventListener("click", () => { fill(PRESETS[b.dataset.preset]); form.requestSubmit(); }));
  $("#reset").addEventListener("click", () => { form.reset(); idle(); errBox.classList.remove("show"); });

  /* ---------- tampilan hasil ---------- */
  const idleHTML = result.innerHTML;
  const idle = () => { result.innerHTML = idleHTML; };
  const LEN = Math.PI * 80;
  const color = b => ({ rendah: "var(--ok)", sedang: "var(--warn)", tinggi: "var(--bad)" }[b]);
  const badgeCls = b => ({ rendah: "ok", sedang: "warn", tinggi: "bad" }[b]);

  function render(r) {
    const pct = (r.probability * 100).toFixed(1).replace(".", ",");
    const maxImp = Math.max(...r.factors.map(f => Math.abs(f.impact)), 0.001);
    const icon = r.risky
      ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M12 9v4m0 4h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/></svg>'
      : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>';
    result.innerHTML = `
      <div class="fade">
        <div class="gauge">
          <svg viewBox="0 0 200 112"><path class="track" d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke-width="16" stroke-linecap="round"/>
            <path class="bar" id="bar" d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke-width="16" stroke="${color(r.band)}"
              stroke-dasharray="${LEN}" stroke-dashoffset="${LEN}"/></svg>
          <div class="center"><div class="pct">${pct}%</div></div>
        </div>
        <div class="gcap">skor probabilitas gagal bayar</div>
        <div class="verdict"><span class="badge ${badgeCls(r.band)}">${icon}${r.label}</span></div>
        <div class="band">Tingkat risiko: <b style="color:${color(r.band)}">${r.band_label}</b> &middot; ambang keputusan ${(r.threshold * 100).toFixed(0)}%</div>
        <div class="advice">${r.advice}</div>
        <div class="factors"><h4>Faktor utama (dibanding nasabah rata-rata)</h4>
          ${r.factors.map(f => `
            <div class="factor"><div class="row"><span>${f.name}</span><em class="${f.direction}">${f.direction === "naik" ? "▲ menaikkan risiko" : "▼ menurunkan risiko"}</em></div>
            <div class="meter"><i class="${f.direction}" data-w="${(Math.abs(f.impact) / maxImp * 100).toFixed(0)}"></i></div></div>`).join("")}
        </div>
        <p class="note">Skor berasal dari model Regresi Logistik yang dilatih dengan SMOTE sehingga cenderung lebih sensitif (skor condong lebih tinggi). Gunakan sebagai alat bantu keputusan, bukan keputusan akhir.</p>
      </div>`;
    requestAnimationFrame(() => requestAnimationFrame(() => {
      $("#bar").style.strokeDashoffset = LEN * (1 - r.probability);
      result.querySelectorAll(".meter i").forEach(i => i.style.width = i.dataset.w + "%");
    }));
    if (matchMedia("(max-width:980px)").matches) result.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  /* ---------- submit ---------- */
  form.addEventListener("submit", async e => {
    e.preventDefault();
    errBox.classList.remove("show");
    form.querySelectorAll(".invalid").forEach(x => x.classList.remove("invalid"));
    const data = Object.fromEntries(new FormData(form).entries());
    const bad = [];
    form.querySelectorAll("input.input").forEach(i => { if (i.value.trim() === "" || isNaN(Number(i.value))) { i.classList.add("invalid"); bad.push(i); } });
    if (bad.length) {
      errBox.textContent = "Lengkapi semua kolom angka dengan nilai yang valid.";
      errBox.classList.add("show"); bad[0].focus(); return;
    }
    btn.disabled = true; btn.classList.add("loading");
    try {
      const res = await fetch("/api/predict", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
      const j = await res.json();
      if (!res.ok || !j.ok) { errBox.innerHTML = (j.errors || ["Terjadi kesalahan."]).join("<br>"); errBox.classList.add("show"); }
      else render(j);
    } catch (err) {
      errBox.textContent = "Tidak dapat menghubungi server. Coba lagi."; errBox.classList.add("show");
    } finally { btn.disabled = false; btn.classList.remove("loading"); }
  });
})();
