/* Morenita Signals, static mode.
   Answers the explorer's three requests (/, /search, /graph) in the browser
   from the files tools/build_static.py writes, using the same rules as
   api/main.py and Recommender.graph. Loaded only by docs/index.html. */
(function () {
  const store = { info: null, works: null, keyIndex: null, neighbors: {} };
  const json = (p) => fetch(p).then((r) => { if (!r.ok) throw new Error(r.statusText); return r.json(); });

  async function works() {
    if (!store.works) {
      store.works = await json('data/works.json');
      store.keyIndex = new Map(store.works.map((w, i) => [w.key, i]));
    }
    return store.works;
  }
  async function info() { return store.info || (store.info = await json('data/info.json')); }
  async function neighbors(m) { return store.neighbors[m] || (store.neighbors[m] = await json(`data/neighbors-${m}.json`)); }

  const ident = (w) => `${String(w.title).trim().toLowerCase()}|${String(w.author ?? 'nan').trim().toLowerCase()}`;
  const card = (w) => {
    const c = { title: w.title, author: w.author ?? null, year: w.year ?? null, domain: w.domain, collection: w.collection, key: w.key };
    if (w.image) c.image = w.image;
    if (w.url) c.url = w.url;
    return c;
  };
  function shared(a, b) {
    const sa = new Map(a.subjects.map((s) => [s.toLowerCase(), s]));
    const out = new Map();
    for (const s of b.subjects) if (sa.has(s.toLowerCase())) out.set(s.toLowerCase(), sa.get(s.toLowerCase()));
    return [...out.values()].sort((x, y) => x.toLowerCase().localeCompare(y.toLowerCase())).slice(0, 5);
  }

  function find(ws, ref) {
    if (store.keyIndex.has(ref)) return store.keyIndex.get(ref);
    const t = ref.trim().toLowerCase();
    for (const test of [(s) => s === t, (s) => s.startsWith(t)]) {
      let best = -1;
      ws.forEach((w, i) => { if (test(w.title.toLowerCase()) && (best < 0 || w.editions > ws[best].editions)) best = i; });
      if (best >= 0) return best;
    }
    return null;
  }

  async function search(q, n) {
    const ws = await works();
    const t = q.trim().toLowerCase();
    if (!t) return { query: q, results: [] };
    const hits = ws.map((w, i) => i).filter((i) => ws[i].title.toLowerCase().includes(t)).sort((a, b) => ws[b].editions - ws[a].editions);
    const out = [], seen = new Set();
    for (const i of hits) {
      const id = ident(ws[i]);
      if (seen.has(id)) continue;
      seen.add(id);
      out.push(card(ws[i]));
      if (out.length === n) break;
    }
    return { query: q, results: out };
  }

  async function graph(ref, m) {
    const [ws, inf] = await Promise.all([works(), info()]);
    const method = m && inf.methods.includes(m) ? m : inf.method;
    const nb = await neighbors(method);
    const idx = find(ws, ref);
    if (idx == null) throw new Error(`Work '${ref}' not found.`);
    const n = 6, second = 2, kinN = Math.max(2, Math.floor(n / 2));
    const nodes = new Map([[ws[idx].key, { ...card(ws[idx]), ring: 0 }]]);
    const edges = [];
    const add = (src, list, ring, kind) => {
      for (const [j, score] of list) {
        const w = ws[j];
        if (!nodes.has(w.key)) nodes.set(w.key, { ...card(w), ring });
        edges.push({ source: ws[src].key, target: w.key, score, shared: shared(ws[src], w), kind, method });
      }
    };
    const first = nb[idx][0].slice(0, n);
    const kin = nb[idx][1].filter(([j]) => ws[j].domain === ws[idx].domain).slice(0, kinN);
    add(idx, first, 1, 'bridge');
    add(idx, kin, 1, 'kin');
    const seen = new Set([ident(ws[idx]), ...first.concat(kin).map(([j]) => ident(ws[j]))]);
    for (const [j] of first) {
      // Like Recommender._neighbors(j, exclude=seen): the exclusions are the
      // center's rings; second-ring picks may repeat across first-ring works.
      const more = [], local = new Set(seen);
      for (const [k, s] of nb[j][0]) {
        if (more.length === second) break;
        if (local.has(ident(ws[k]))) continue;
        local.add(ident(ws[k]));
        more.push([k, s]);
      }
      add(j, more, 2, 'bridge');
    }
    return { center: ws[idx].key, nodes: [...nodes.values()], edges, method };
  }

  window.signalsStatic = async function (path) {
    const u = new URL(path, location.href);
    if (u.pathname.endsWith('/search')) return search(u.searchParams.get('q') || '', Number(u.searchParams.get('n') || 10));
    if (u.pathname.endsWith('/graph')) return graph(u.searchParams.get('ref') || '', u.searchParams.get('method'));
    return info();
  };
})();
