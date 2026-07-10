(function () {
  "use strict";

  var storageKey = "audo_booking_context";
  var recaptchaPromise = null;

  function safeSessionGet() {
    try {
      var raw = window.sessionStorage.getItem(storageKey);
      return raw ? JSON.parse(raw) : null;
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

  function safeSessionRemove() {
    try {
      window.sessionStorage.removeItem(storageKey);
    } catch (error) {
      return;
    }
  }

  function loadRecaptcha(siteKey) {
    if (!siteKey) {
      return Promise.resolve("");
    }
    if (window.grecaptcha && window.grecaptcha.ready) {
      return executeRecaptcha(siteKey);
    }
    if (!recaptchaPromise) {
      recaptchaPromise = new Promise(function (resolve, reject) {
        var script = document.createElement("script");
        script.src = "https://www.google.com/recaptcha/api.js?render=" + encodeURIComponent(siteKey);
        script.async = true;
        script.defer = true;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
      });
    }
    return recaptchaPromise.then(function () {
      return executeRecaptcha(siteKey);
    });
  }

  function executeRecaptcha(siteKey) {
    return new Promise(function (resolve, reject) {
      if (!window.grecaptcha || !window.grecaptcha.ready) {
        reject(new Error("Spam protection did not load."));
        return;
      }
      window.grecaptcha.ready(function () {
        window.grecaptcha.execute(siteKey, { action: "discovery_request" }).then(resolve).catch(reject);
      });
    });
  }

  function responseJson(response) {
    return response.json().catch(function () {
      return {};
    }).then(function (payload) {
      if (!response.ok) {
        var error = new Error(payload.error || "Something went wrong. Please try again.");
        error.payload = payload;
        error.status = response.status;
        throw error;
      }
      return payload;
    });
  }

  function postJson(url, payload) {
    return fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Accept": "application/json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    }).then(responseJson);
  }

  function makeScheduler() {
    var section = document.createElement("section");
    section.className = "booking-step";
    section.setAttribute("data-booking-step", "");
    section.setAttribute("aria-labelledby", "booking-step-title");
    section.hidden = true;
    section.innerHTML = [
      '<div class="booking-step-header">',
      '  <p class="booking-step-kicker">Step 2 of 2 · Pick a time</p>',
      '  <h3 id="booking-step-title" tabindex="-1" data-booking-heading>When would you like to talk?</h3>',
      '  <p class="booking-step-copy">Choose any open 30-minute slot. Times are shown in Central Time.</p>',
      '</div>',
      '<ul class="booking-policies" aria-label="Booking details">',
      '  <li>Monday–Saturday</li>',
      '  <li>24-hour notice</li>',
      '  <li>Google Meet</li>',
      '</ul>',
      '<p class="booking-loading" data-booking-loading>Loading available times…</p>',
      '<p class="booking-alert" role="alert" data-booking-alert hidden></p>',
      '<div data-booking-picker hidden>',
      '  <div class="booking-date-list" role="tablist" aria-label="Available dates" data-booking-dates></div>',
      '  <div class="booking-time-group">',
      '    <p class="booking-time-heading" data-booking-time-heading></p>',
      '    <div class="booking-time-list" aria-label="Available times" data-booking-times></div>',
      '  </div>',
      '</div>',
      '<div class="booking-confirmation" data-booking-confirmation hidden>',
      '  <p>You chose<strong data-booking-selection></strong></p>',
      '  <button class="button primary" type="button" data-booking-confirm>Book this time</button>',
      '</div>',
      '<div class="booking-success" data-booking-success hidden>',
      '  <span class="booking-success-mark" aria-hidden="true">✓</span>',
      '  <h4>You\'re booked.</h4>',
      '  <p data-booking-success-time></p>',
      '  <p>Your calendar invite is on the way. It includes the Google Meet link and the note you sent me.</p>',
      '  <a class="button primary" href="#" target="_blank" rel="noopener noreferrer" data-booking-meet hidden>Open Google Meet</a>',
      '</div>',
      '<p class="booking-fallback-line" data-booking-fallback hidden>Calendar not working? <a href="#" target="_blank" rel="noopener noreferrer">Book through Google instead</a>.</p>'
    ].join("");
    return section;
  }

  function initForm(form, formIndex) {
    var siteKey = window.AUDO_RECAPTCHA_SITE_KEY || "";
    var submitButton = form.querySelector("button[type='submit']");
    var submitLabel = submitButton ? submitButton.textContent : "Continue to scheduling";
    var status = form.querySelector(".form-status");
    var note = form.querySelector(".form-note");
    var grid = form.querySelector(".form-grid");
    var scheduler = makeScheduler();
    var heading = scheduler.querySelector("[data-booking-heading]");
    var loading = scheduler.querySelector("[data-booking-loading]");
    var alertBox = scheduler.querySelector("[data-booking-alert]");
    var picker = scheduler.querySelector("[data-booking-picker]");
    var dateList = scheduler.querySelector("[data-booking-dates]");
    var timeHeading = scheduler.querySelector("[data-booking-time-heading]");
    var timeList = scheduler.querySelector("[data-booking-times]");
    var confirmation = scheduler.querySelector("[data-booking-confirmation]");
    var selectionLabel = scheduler.querySelector("[data-booking-selection]");
    var confirmButton = scheduler.querySelector("[data-booking-confirm]");
    var success = scheduler.querySelector("[data-booking-success]");
    var successTime = scheduler.querySelector("[data-booking-success-time]");
    var meetLink = scheduler.querySelector("[data-booking-meet]");
    var fallback = scheduler.querySelector("[data-booking-fallback]");
    var fallbackLink = fallback.querySelector("a");
    var context = null;
    var availability = null;
    var selectedDay = null;
    var selectedSlot = null;

    heading.id = "booking-step-title-" + formIndex;
    scheduler.setAttribute("aria-labelledby", heading.id);
    form.appendChild(scheduler);

    // The page's original reCAPTCHA enhancement remains the non-AJAX fallback.
    // This flag lets this branded flow own submission when JavaScript is available.
    form.dataset.recaptchaSubmitted = "true";

    function setFallback(url) {
      var target = url || window.AUDO_GOOGLE_CALENDAR_BOOKING_URL || "";
      if (!target) {
        fallback.hidden = true;
        return;
      }
      fallbackLink.href = target;
      fallback.hidden = false;
    }

    function setAlert(message) {
      alertBox.textContent = message || "";
      alertBox.hidden = !message;
    }

    function resetSubmit(message) {
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.textContent = submitLabel;
      }
      form.removeAttribute("aria-busy");
      if (status) {
        status.setAttribute("role", "alert");
        status.classList.add("is-error");
        status.textContent = message;
      }
    }

    function showScheduler() {
      if (grid) {
        grid.hidden = true;
      }
      if (submitButton) {
        submitButton.hidden = true;
      }
      if (status) {
        status.hidden = true;
      }
      if (note) {
        note.hidden = true;
      }
      form.classList.add("is-scheduling");
      form.removeAttribute("aria-busy");
      scheduler.hidden = false;
      window.setTimeout(function () {
        heading.focus({ preventScroll: true });
        scheduler.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }, 20);
    }

    function renderSuccess(booking) {
      loading.hidden = true;
      picker.hidden = true;
      confirmation.hidden = true;
      setAlert("");
      success.hidden = false;
      successTime.textContent = booking.date_label + " · " + booking.time_label + " · " + booking.timezone_label;
      if (booking.meet_url) {
        meetLink.href = booking.meet_url;
        meetLink.hidden = false;
      } else {
        meetLink.hidden = true;
      }
      safeSessionRemove();
      success.querySelector("h4").focus && success.querySelector("h4").focus();
    }

    function selectSlot(slot, button) {
      selectedSlot = slot;
      Array.prototype.forEach.call(timeList.querySelectorAll("button"), function (item) {
        item.setAttribute("aria-pressed", item === button ? "true" : "false");
      });
      selectionLabel.textContent = selectedDay.label + " at " + slot.label + " Central Time";
      confirmation.hidden = false;
      setAlert("");
    }

    function renderTimes(day) {
      selectedDay = day;
      selectedSlot = null;
      confirmation.hidden = true;
      timeHeading.textContent = day.label + " · Central Time";
      timeList.textContent = "";
      day.slots.forEach(function (slot) {
        var button = document.createElement("button");
        button.type = "button";
        button.className = "booking-time";
        button.textContent = slot.label;
        button.setAttribute("aria-pressed", "false");
        button.addEventListener("click", function () {
          selectSlot(slot, button);
        });
        timeList.appendChild(button);
      });
    }

    function selectDay(day, button) {
      Array.prototype.forEach.call(dateList.querySelectorAll("button"), function (item) {
        var selected = item === button;
        item.setAttribute("aria-selected", selected ? "true" : "false");
        item.tabIndex = selected ? 0 : -1;
      });
      renderTimes(day);
    }

    function renderAvailability(payload) {
      availability = payload;
      loading.hidden = true;
      setFallback(payload.fallback_url);
      if (payload.booked && payload.booking) {
        renderSuccess(payload.booking);
        return;
      }
      if (!payload.days || !payload.days.length) {
        picker.hidden = true;
        setAlert("I don't have an open time in the next 30 days. You can book through Google instead, or leave your note and I'll follow up.");
        return;
      }

      dateList.textContent = "";
      payload.days.forEach(function (day, index) {
        var button = document.createElement("button");
        button.type = "button";
        button.className = "booking-date";
        button.setAttribute("role", "tab");
        button.setAttribute("aria-label", day.label);
        button.setAttribute("aria-selected", index === 0 ? "true" : "false");
        button.tabIndex = index === 0 ? 0 : -1;

        var weekday = document.createElement("span");
        weekday.className = "booking-date-weekday";
        weekday.textContent = day.weekday;
        var dayNumber = document.createElement("span");
        dayNumber.className = "booking-date-day";
        dayNumber.textContent = day.day;
        button.appendChild(weekday);
        button.appendChild(dayNumber);
        button.addEventListener("click", function () {
          selectDay(day, button);
        });
        dateList.appendChild(button);
      });
      picker.hidden = false;
      renderTimes(payload.days[0]);
    }

    function loadAvailability() {
      loading.hidden = false;
      picker.hidden = true;
      confirmation.hidden = true;
      success.hidden = true;
      setAlert("");
      postJson("/api/availability", {
        request_id: context.request_id,
        booking_token: context.booking_token
      }).then(renderAvailability).catch(function (error) {
        loading.hidden = true;
        setAlert(error.message || "I couldn't load the calendar. Please try again or use the Google booking page.");
        setFallback(error.payload && error.payload.fallback_url);
      });
    }

    function submitLead() {
      if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = "Sending your note…";
      }
      form.setAttribute("aria-busy", "true");
      if (status) {
        status.hidden = false;
        status.classList.remove("is-error");
        status.setAttribute("role", "status");
        status.textContent = "One moment…";
      }

      loadRecaptcha(siteKey).then(function (token) {
        var tokenInput = form.querySelector("input[name='recaptcha_token']");
        if (tokenInput) {
          tokenInput.value = token;
        }
        return fetch(form.action, {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
          },
          body: new URLSearchParams(new FormData(form)).toString()
        }).then(responseJson);
      }).then(function (payload) {
        if (!payload.request_id || !payload.booking_token) {
          window.location.assign(payload.fallback_url || "/thank-you");
          return;
        }
        context = {
          request_id: payload.request_id,
          booking_token: payload.booking_token,
          fallback_url: payload.fallback_url || "",
          created_at: Date.now()
        };
        safeSessionSet(context);
        setFallback(context.fallback_url);
        showScheduler();
        loadAvailability();
      }).catch(function (error) {
        resetSubmit(error.message || "I couldn't send your note. Please try again.");
      });
    }

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      if (form.classList.contains("is-scheduling")) {
        return;
      }
      submitLead();
    });

    confirmButton.addEventListener("click", function () {
      if (!selectedSlot || !context) {
        return;
      }
      confirmButton.disabled = true;
      confirmButton.textContent = "Booking your time…";
      setAlert("");
      postJson("/api/book", {
        request_id: context.request_id,
        booking_token: context.booking_token,
        start: selectedSlot.start
      }).then(function (payload) {
        renderSuccess(payload.booking);
      }).catch(function (error) {
        confirmButton.disabled = false;
        confirmButton.textContent = "Book this time";
        setAlert(error.message || "I couldn't book that time. Please choose another one.");
        setFallback(error.payload && error.payload.fallback_url);
        if (error.payload && error.payload.refresh_availability) {
          window.setTimeout(loadAvailability, 900);
        }
      });
    });

    var stored = safeSessionGet();
    if (stored && stored.request_id && stored.booking_token && Date.now() - stored.created_at < 72 * 60 * 60 * 1000) {
      context = stored;
      setFallback(stored.fallback_url);
      showScheduler();
      loadAvailability();
    }
  }

  Array.prototype.forEach.call(document.querySelectorAll("[data-inline-booking]"), function (form, index) {
    initForm(form, index + 1);
  });
}());
