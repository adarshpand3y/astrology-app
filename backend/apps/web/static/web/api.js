// Minimal API client mirroring what the mobile app will do: JWT in storage,
// automatic refresh on 401, uniform error envelope.
const API = "/api/v1";

const auth = {
  get access() { return localStorage.getItem("access"); },
  get refresh() { return localStorage.getItem("refresh"); },
  save(t) {
    if (t.access) localStorage.setItem("access", t.access);
    if (t.refresh) localStorage.setItem("refresh", t.refresh);
    if (t.user) localStorage.setItem("user", JSON.stringify(t.user));
  },
  clear() { ["access", "refresh", "user"].forEach(k => localStorage.removeItem(k)); },
  user() { try { return JSON.parse(localStorage.getItem("user")); } catch { return null; } },
};

class ApiError extends Error {
  constructor(status, body) {
    super(body?.error?.message || `HTTP ${status}`);
    this.status = status;
    this.body = body;
  }
}

async function tryRefresh() {
  if (!auth.refresh) return false;
  const r = await fetch(`${API}/auth/token/refresh/`, {
    method: "POST", headers: { "Content-Type": "application/json", "X-App-Platform": "web" },
    body: JSON.stringify({ refresh: auth.refresh }),
  });
  if (!r.ok) return false;
  auth.save(await r.json());
  return true;
}

async function api(path, { method = "GET", body, query, retry = true } = {}) {
  let url = `${API}${path}`;
  if (query) url += "?" + new URLSearchParams(query).toString();
  const headers = { "Accept": "application/json", "X-App-Platform": "web" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth.access) headers["Authorization"] = `Bearer ${auth.access}`;
  const r = await fetch(url, { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined });
  if (r.status === 401 && retry && await tryRefresh()) return api(path, { method, body, query, retry: false });
  if (r.status === 401 && !path.startsWith("/auth/")) { auth.clear(); location.href = "/ui/"; }
  const text = await r.text();
  const data = text ? JSON.parse(text) : null;
  if (!r.ok) throw new ApiError(r.status, data);
  return data;
}

function requireLogin() { if (!auth.access) location.href = "/ui/"; }

async function logout() {
  try { await api("/auth/logout/", { method: "POST", body: { refresh: auth.refresh } }); } catch { }
  auth.clear(); location.href = "/ui/";
}

// --- helpers ---------------------------------------------------------------------
const $ = (sel, el = document) => el.querySelector(sel);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmtDate = iso => iso ? iso.replace("T", " ").slice(0, 16) : "—";
const num = (v, d = 2) => (v === null || v === undefined) ? "—" : Number(v).toFixed(d);

function showError(el, err) {
  const details = err.body?.error?.details;
  el.innerHTML = `<div class="error">${esc(err.message)}${details ? `<pre>${esc(JSON.stringify(details, null, 1))}</pre>` : ""}</div>`;
}

const PLANET_ABBR = { Su: "Su", Mo: "Mo", Ma: "Ma", Me: "Me", Ju: "Ju", Ve: "Ve", Sa: "Sa", Ra: "Ra", Ke: "Ke" };
const SIGN_SHORT = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"];

// --- chart drawing ---------------------------------------------------------------
// varga: {ascendant:{sign_index}, planets:[{code, sign_index, house}]}, extra: {code: label suffix}
function northIndianSVG(varga, extra = {}) {
  const P = [
    [[200, 0], [300, 100], [200, 200], [100, 100]], [[0, 0], [200, 0], [100, 100]],
    [[0, 0], [100, 100], [0, 200]], [[0, 200], [100, 100], [200, 200], [100, 300]],
    [[0, 200], [100, 300], [0, 400]], [[0, 400], [100, 300], [200, 400]],
    [[200, 400], [100, 300], [200, 200], [300, 300]], [[200, 400], [300, 300], [400, 400]],
    [[400, 400], [300, 300], [400, 200]], [[400, 200], [300, 300], [200, 200], [300, 100]],
    [[400, 200], [300, 100], [400, 0]], [[400, 0], [300, 100], [200, 0]],
  ];
  const asc = varga.ascendant.sign_index;
  let svg = `<svg viewBox="-2 -2 404 404" class="chart">`;
  P.forEach((poly, i) => {
    const house = i + 1;
    const sign = ((asc - 1 + i) % 12) + 1;
    const cx = poly.reduce((a, p) => a + p[0], 0) / poly.length;
    const cy = poly.reduce((a, p) => a + p[1], 0) / poly.length;
    const occ = varga.planets.filter(p => p.house === house).map(p => p.code + (extra[p.code] || ""));
    if (house === 1) occ.unshift("Asc");
    svg += `<polygon points="${poly.map(p => p.join(",")).join(" ")}" class="house${house === 1 ? " lagna" : ""}"/>`;
    svg += `<text x="${cx}" y="${cy - 14 - (occ.length > 2 ? 6 : 0)}" class="signnum">${sign}</text>`;
    occ.forEach((o, k) => {
      const row = Math.floor(k / 2), col = k % 2;
      const n = Math.min(2, occ.length - row * 2);
      svg += `<text x="${cx + (n === 2 ? (col ? 16 : -16) : 0)}" y="${cy + 4 + row * 15}" class="pl">${esc(o)}</text>`;
    });
  });
  return svg + `</svg>`;
}

function southIndianSVG(varga, extra = {}) {
  const pos = { 12: [0, 0], 1: [1, 0], 2: [2, 0], 3: [3, 0], 4: [3, 1], 5: [3, 2], 6: [3, 3], 7: [2, 3], 8: [1, 3], 9: [0, 3], 10: [0, 2], 11: [0, 1] };
  const asc = varga.ascendant.sign_index;
  let svg = `<svg viewBox="-2 -2 404 404" class="chart">`;
  for (let sign = 1; sign <= 12; sign++) {
    const [c, r] = pos[sign];
    const x = c * 100, y = r * 100;
    const occ = varga.planets.filter(p => p.sign_index === sign).map(p => p.code + (extra[p.code] || ""));
    if (sign === asc) occ.unshift("Asc");
    svg += `<rect x="${x}" y="${y}" width="100" height="100" class="house${sign === asc ? " lagna" : ""}"/>`;
    svg += `<text x="${x + 6}" y="${y + 14}" class="signnum" text-anchor="start">${SIGN_SHORT[sign - 1]}</text>`;
    occ.forEach((o, k) => {
      svg += `<text x="${x + 28 + (k % 2) * 44}" y="${y + 38 + Math.floor(k / 2) * 18}" class="pl">${esc(o)}</text>`;
    });
  }
  svg += `<text x="200" y="205" class="center">${esc(varga.code)} ${esc(varga.name)}</text>`;
  return svg + `</svg>`;
}
