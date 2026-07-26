(function () {
  "use strict";

  var storageKey = "audo_attribution_context_v1";
  var campaignKeys = [
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
    "audo_campaign"
  ];

  function safeParseUrl(value, base) {
    if (!value) {
      return null;
    }
    try {
      var parsed = new URL(value, base || window.location.href);
      if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
        return null;
      }
      return parsed;
    } catch (error) {
      return null;
    }
  }

  function safeUrl(value, base, originOnly) {
    var parsed = safeParseUrl(value, base);
    if (!parsed) {
      return "";
    }
    return parsed.origin + (originOnly ? "/" : (parsed.pathname || "/"));
  }

  function campaignValues(parsed) {
    var values = {};
    campaignKeys.forEach(function (key) {
      var value = parsed.searchParams.get(key);
      if (value) {
        values[key] = value.slice(0, 160);
      }
    });
    return values;
  }

  function safeSessionGet() {
    try {
      var raw = window.sessionStorage.getItem(storageKey);
      var parsed = raw ? JSON.parse(raw) : null;
      return parsed && typeof parsed === "object" ? parsed : null;
    } catch (error) {
      return null;
    }
  }

  function safeSessionSet(value) {
    try {
      window.sessionStorage.setItem(storageKey, JSON.stringify(value));
    } catch (error) {
      return;
    }
  }

  function currentTouch() {
    var current = safeParseUrl(window.location.href);
    var referrer = safeParseUrl(document.referrer, window.location.href);
    var values = current ? campaignValues(current) : {};
    var externalReferrer = "";

    if (current && referrer && referrer.origin !== current.origin) {
      externalReferrer = safeUrl(referrer.href, "", true);
    }

    return Object.assign({
      captured_at: new Date().toISOString(),
      landing_url: current ? safeUrl(current.href) : "",
      referring_url: externalReferrer
    }, values);
  }

  function isAttributable(touch) {
    return Boolean(
      touch.referring_url ||
      touch.utm_source ||
      touch.utm_medium ||
      touch.utm_campaign ||
      touch.utm_content ||
      touch.audo_campaign
    );
  }

  function capture() {
    var touch = currentTouch();
    var stored = safeSessionGet();
    var context = stored && stored.first && stored.latest
      ? stored
      : { first: touch, latest: touch };

    if (stored && stored.first && stored.latest && isAttributable(touch)) {
      context = { first: stored.first, latest: touch };
    }

    safeSessionSet(context);
    return context;
  }

  var inMemoryContext = capture();

  function getContext() {
    return safeSessionGet() || inMemoryContext || capture();
  }

  function upsertHidden(form, name, value) {
    var field = form.querySelector("[name='" + name + "']");
    if (!field) {
      field = document.createElement("input");
      field.type = "hidden";
      field.name = name;
      form.appendChild(field);
    }
    field.value = value;
  }

  function applyToForm(form) {
    var context = getContext();
    upsertHidden(form, "first_touch", JSON.stringify(context.first || {}));
    upsertHidden(form, "latest_touch", JSON.stringify(context.latest || context.first || {}));
  }

  window.AUDO_ATTRIBUTION = {
    applyToForm: applyToForm,
    capture: capture,
    getContext: getContext
  };
}());
