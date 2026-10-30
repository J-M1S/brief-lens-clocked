// Focused logic tests with a tiny in-memory DOM; no browser or network is used.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

class Element {
  constructor() { this.children = []; this.events = {}; this.hidden = false; this.value = ''; this.checked = false; this.disabled = false; this.textContent = ''; this.firstChild = { textContent: '' }; }
  addEventListener(name, callback) { this.events[name] = callback; }
  dispatchEvent(event) { this.events[event.type]?.(event); }
  append(child) { this.children.push(child); }
  replaceChildren(...items) { this.children = items; }
}
const ids = ['brief','count','consent','error','analyze','sample','results','empty','badge','notice','facts','flags','question'];
const elements = Object.fromEntries(ids.map(id => [id, new Element()]));
const fixture = JSON.parse(fs.readFileSync('live-check-fictional.json', 'utf8'));
const context = vm.createContext({
  document: { querySelector: selector => elements[selector.slice(1)], createElement: () => new Element() },
  Event: class { constructor(type) { this.type = type; } },
  fetch: async path => path === '/live-check-fictional.json'
    ? { ok: true, json: async () => fixture }
    : { ok: false, json: async () => ({ error: 'Connection unavailable' }) },
});
vm.runInContext(fs.readFileSync('app.js', 'utf8'), context);

(async () => {
  await elements.sample.events.click();
  assert.equal(elements.badge.textContent, 'RECORDED EXAMPLE');
  assert.equal(elements.facts.children[0].children[1].textContent, '“$240”');
  assert.equal(elements.facts.children[1].children[1].textContent, 'Not established — ask');
  assert.equal(elements.results.hidden, false);
  assert.equal(vm.runInContext("verifiedSpan('😀A', {value:'A',start:1,end:2})", context), true);
  assert.equal(vm.runInContext("verifiedSpan('😀A', {value:'B',start:1,end:2})", context), false);

  elements.brief.value = 'An unrelated new brief';
  elements.brief.dispatchEvent({type:'input'});
  assert.equal(elements.results.hidden, true, 'old results must not remain visible for new input');
  elements.consent.checked = true;
  await elements.analyze.events.click();
  assert.equal(elements.results.hidden, true, 'failed requests must not reveal stale results');
  assert.equal(elements.error.textContent, 'Connection unavailable');
  console.log('UI logic: recorded response, Unicode source spans, and stale-result handling passed.');
})().catch(err => { console.error(err); process.exitCode = 1; });
