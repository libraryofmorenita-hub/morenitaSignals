// Runs docs/static-api.js in Node against a folder of built data and prints
// the graph for every key given, as JSON. Used by tests/test_static.py.
// usage: node static_harness.js <static-api.js> <docs folder> <method> <key>...
const fs = require('fs');
const path = require('path');
const [api, docs, method, ...keys] = process.argv.slice(2);
globalThis.window = globalThis;
globalThis.location = { href: 'http://localhost/' };
globalThis.fetch = async (p) => {
  const file = path.join(docs, String(p));
  return { ok: fs.existsSync(file), statusText: 'missing ' + p, json: async () => JSON.parse(fs.readFileSync(file, 'utf8')) };
};
eval(fs.readFileSync(api, 'utf8'));
(async () => {
  const out = {};
  for (const k of keys) out[k] = await window.signalsStatic('graph?ref=' + encodeURIComponent(k) + '&method=' + method);
  process.stdout.write(JSON.stringify(out));
})().catch((e) => { console.error(e); process.exit(1); });
