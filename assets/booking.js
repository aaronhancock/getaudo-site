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
      '  <p class="booking-step-copy">Your note is saved. Choose any open 30-minute slot. Times are shown in Central Time.</p>',
      '</div>',
      '<ul class="booking-policies" aria-label="Booking details">',
      '  <li>Monday–Saturday</li>',
      '  <li>24-hour notice</li>',
      '  <li>Google Meet</li>',
      '</ul>',
      '<p class="booking-loading" role="status" aria-live="polite" data-booking-loading>Loading available times…</p>',
      '<p class="booking-alert" role="alert" data-booking-alert hidden></p>',
      '<div data-booking-picker hidden>',
      '  <div class="booking-mobile-date-field">',
      '    <label for="booking-date-select">Choose a date</label>',
      '    <select id="booking-date-select" data-booking-date-select></select>',
      '  </div>',
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
      '  <h4 tabindex="-1">You\'re booked.</h4>',
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
    var dateSelect = scheduler.querySelector("[data-booking-date-select]");
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
    var fieldErrors = {};

    heading.id = "booking-step-title-" + formIndex;
    scheduler.setAttribute("aria-labelledby", heading.id);
    dateSelect.id = "booking-date-select-" + formIndex;
    scheduler.querySelector("label[for='booking-date-select']").setAttribute("for", dateSelect.id);
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

    function clearFieldError(field) {
      if (!field || !field.name) {
        return;
      }
      field.removeAttribute("aria-invalid");
      var error = fieldErrors[field.name];
      if (error) {
        error.remove();
        delete fieldErrors[field.name];
      }
      var describedBy = (field.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean);
      field.setAttribute("aria-describedby", describedBy.filter(function (id) {
        return id.indexOf("field-error-") !== 0;
      }).join(" "));
    }

    function showFieldError(fieldName, message) {
      var field = form.querySelector("[name='" + fieldName + "']");
      if (!field) {
        return false;
      }
      clearFieldError(field);
      var error = document.createElement("p");
      error.className = "field-error";
      error.id = "field-error-" + formIndex + "-" + fieldName;
      error.textContent = message;
      field.setAttribute("aria-invalid", "true");
      var describedBy = (field.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean);
      describedBy.push(error.id);
      field.setAttribute("aria-describedby", describedBy.join(" "));
      field.insertAdjacentElement("afterend", error);
      fieldErrors[fieldName] = error;
      field.focus();
      return false;
    }

    function validateLeadFields() {
      var name = form.querySelector("[name='name']");
      var email = form.querySelector("[name='email']");
      var message = form.querySelector("[name='message']");
      [name, email, message].forEach(clearFieldError);
      if (!name || !name.value.trim()) {
        return showFieldError("name", "Please enter your name.");
      }
      if (!email || !email.value.trim() || !email.validity.valid) {
        return showFieldError("email", "Enter an email address such as name@example.com.");
      }
      if (!message || !message.value.trim()) {
        return showFieldError("message", "Tell me a little about what is happening.");
      }
      return true;
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
      if (availability && availability.days) {
        dateSelect.value = String(availability.days.indexOf(day));
      }
      renderTimes(day);
    }

    function renderAvailability(payload) {
      availability = payload;
      scheduler.removeAttribute("aria-busy");
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
      dateSelect.textContent = "";
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

        var option = document.createElement("option");
        option.value = String(index);
        option.textContent = day.label;
        dateSelect.appendChild(option);
      });
      dateSelect.value = "0";
      picker.hidden = false;
      renderTimes(payload.days[0]);
    }

    dateSelect.addEventListener("change", function () {
      if (!availability || !availability.days) {
        return;
      }
      var index = Number(dateSelect.value);
      var day = availability.days[index];
      if (!day) {
        return;
      }
      var buttons = dateList.querySelectorAll("button");
      selectDay(day, buttons[index]);
    });

    function loadAvailability() {
      scheduler.setAttribute("aria-busy", "true");
      loading.hidden = false;
      picker.hidden = true;
      confirmation.hidden = true;
      success.hidden = true;
      setAlert("");
      postJson("/api/availability", {
        request_id: context.request_id,
        booking_token: context.booking_token
      }).then(renderAvailability).catch(function (error) {
        scheduler.removeAttribute("aria-busy");
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
        var message = error.message || "I couldn't send your note. Please try again.";
        resetSubmit(message);
        if (/name/i.test(message)) {
          showFieldError("name", message);
        } else if (/email/i.test(message)) {
          showFieldError("email", message);
        } else if (/what's going on|tell me|message/i.test(message)) {
          showFieldError("message", message);
        }
      });
    }

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      if (form.classList.contains("is-scheduling")) {
        return;
      }
      if (!validateLeadFields()) {
        return;
      }
      submitLead();
    });

    Array.prototype.forEach.call(form.querySelectorAll("[name='name'], [name='email'], [name='message']"), function (field) {
      field.addEventListener("input", function () {
        clearFieldError(field);
      });
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
