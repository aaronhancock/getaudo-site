const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const source = fs.readFileSync(
  path.join(__dirname, "..", "assets", "attribution.js"),
  "utf8"
);

function storageFor(values, broken = false) {
  return {
    getItem(key) {
      if (broken) {
        throw new Error("storage unavailable");
      }
      return Object.prototype.hasOwnProperty.call(values, key) ? values[key] : null;
    },
    setItem(key, value) {
      if (broken) {
        throw new Error("storage unavailable");
      }
      values[key] = value;
    }
  };
}

function runPage({ href, referrer = "", values = {}, brokenStorage = false }) {
  const document = {
    referrer,
    createElement() {
      return {};
    }
  };
  const window = {
    location: { href },
    sessionStorage: storageFor(values, brokenStorage)
  };
  vm.runInNewContext(source, {
    Date,
    JSON,
    Object,
    URL,
    document,
    window
  });
  return { api: window.AUDO_ATTRIBUTION, document, values };
}

test("captures only allowlisted campaign values and privacy-minimized URLs", () => {
  const { api } = runPage({
    href: "https://getaudo.com/services/fix-a-broken-contact-form?utm_source=linkedin&utm_medium=direct&utm_campaign=lead-flow&utm_content=form&email=private%40example.com#gated",
    referrer: "https://www.linkedin.com/feed/?tracking=secret#post"
  });
  const context = api.getContext();

  assert.equal(
    context.first.landing_url,
    "https://getaudo.com/services/fix-a-broken-contact-form"
  );
  assert.equal(context.first.referring_url, "https://www.linkedin.com/");
  assert.equal(context.first.utm_source, "linkedin");
  assert.equal(context.first.utm_content, "form");
  assert.equal(context.first.email, undefined);
});

test("internal navigation preserves first touch and does not replace latest", () => {
  const values = {};
  const first = runPage({
    href: "https://getaudo.com/?utm_source=partner&utm_campaign=referral",
    referrer: "https://partner.example/recommendations",
    values
  }).api.getContext();
  const second = runPage({
    href: "https://getaudo.com/services/fix-a-broken-contact-form",
    referrer: "https://getaudo.com/",
    values
  }).api.getContext();

  assert.deepEqual(second.first, first.first);
  assert.deepEqual(second.latest, first.latest);
});

test("later explicit campaign updates latest but never first", () => {
  const values = {};
  const first = runPage({
    href: "https://getaudo.com/",
    values
  }).api.getContext();
  const second = runPage({
    href: "https://getaudo.com/?utm_source=linkedin&utm_campaign=followup",
    referrer: "https://getaudo.com/services/fix-a-broken-contact-form",
    values
  }).api.getContext();

  assert.deepEqual(second.first, first.first);
  assert.equal(second.latest.utm_source, "linkedin");
  assert.equal(second.latest.utm_campaign, "followup");
});

test("storage failure still permits hidden attribution fields", () => {
  const { api } = runPage({
    href: "https://getaudo.com/?audo_campaign=warm_intro",
    brokenStorage: true
  });
  const fields = {};
  const form = {
    querySelector(selector) {
      const match = selector.match(/name='([^']+)'/);
      return match ? fields[match[1]] || null : null;
    },
    appendChild(field) {
      fields[field.name] = field;
    }
  };

  api.applyToForm(form);

  assert.equal(JSON.parse(fields.first_touch.value).audo_campaign, "warm_intro");
  assert.equal(JSON.parse(fields.latest_touch.value).audo_campaign, "warm_intro");
});
