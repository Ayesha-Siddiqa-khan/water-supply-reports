/**
 * UploadProgressBar — reusable upload progress UI for all upload forms.
 *
 * Usage: add data-upload-progress="true" to any <form> that uploads files.
 * The form must POST to a server endpoint that returns JSON when the request
 * header X-Requested-With: XMLHttpRequest is present.
 *
 * Expected JSON response: { "ok": true, "redirect": "/path", "message": "..." }
 * or  { "ok": false, "error": "..." }.
 */
(function () {
  'use strict';

  /* ── SVG icons ─────────────────────────────────────────── */
  var ICONS = {
    upload:
      '<svg viewBox="0 0 24 24" fill="none" stroke="#0fd4b0" stroke-width="2"><path d="M12 16V4M8 8l4-4 4 4"/><path d="M20 16v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2"/></svg>',
    processing:
      '<svg viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>',
    success:
      '<svg viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>',
    error:
      '<svg viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/></svg>',
  };

  /* ── Overlay builder ───────────────────────────────────── */
  function createOverlay() {
    var el = document.createElement('div');
    el.className = 'upload-progress-overlay';
    el.innerHTML =
      '<div class="upload-progress-card">' +
        '<div class="upload-progress-icon uploading" data-role="icon">' + ICONS.upload + '</div>' +
        '<div class="upload-progress-title" data-role="title">Uploading file...</div>' +
        '<div class="upload-progress-status" data-role="status">Preparing upload</div>' +
        '<div class="upload-progress-bar-track"><div class="upload-progress-bar-fill" data-role="bar"></div></div>' +
        '<div class="upload-progress-percent" data-role="percent"></div>' +
      '</div>';
    document.body.appendChild(el);
    requestAnimationFrame(function () { el.classList.add('visible'); });
    return el;
  }

  function updateOverlay(overlay, state, title, status, pct) {
    if (!overlay) return;
    var icon = overlay.querySelector('[data-role="icon"]');
    var titleEl = overlay.querySelector('[data-role="title"]');
    var statusEl = overlay.querySelector('[data-role="status"]');
    var bar = overlay.querySelector('[data-role="bar"]');
    var percent = overlay.querySelector('[data-role="percent"]');

    icon.className = 'upload-progress-icon ' + state;
    icon.innerHTML = ICONS[state] || '';
    if (titleEl) titleEl.textContent = title || '';
    if (statusEl) statusEl.textContent = status || '';

    if (state === 'uploading' && typeof pct === 'number') {
      bar.className = 'upload-progress-bar-fill';
      bar.style.width = pct + '%';
      if (percent) percent.textContent = pct + '%';
    } else if (state === 'processing') {
      bar.className = 'upload-progress-bar-fill indeterminate';
      bar.style.width = '';
      if (percent) percent.textContent = '';
    } else {
      bar.className = 'upload-progress-bar-fill';
      bar.style.width = state === 'success' ? '100%' : '0%';
      if (percent) percent.textContent = '';
    }
  }

  function removeOverlay(overlay) {
    if (!overlay) return;
    overlay.classList.remove('visible');
    setTimeout(function () { overlay.remove(); }, 300);
  }

  /* ── Toast notification ────────────────────────────────── */
  function showToast(message, isError) {
    var existing = document.getElementById('upload-toast');
    if (existing) existing.remove();
    var el = document.createElement('div');
    el.id = 'upload-toast';
    el.style.cssText =
      'position:fixed;top:20px;right:20px;z-index:10001;' +
      'padding:12px 20px;border-radius:8px;font-size:13px;font-weight:600;' +
      'box-shadow:0 8px 24px rgba(0,0,0,0.3);max-width:400px;' +
      'animation:toastIn 0.35s ease-out both;';
    if (isError) {
      el.style.background = 'rgba(239,68,68,0.15)';
      el.style.border = '1px solid rgba(239,68,68,0.4)';
      el.style.color = '#fca5a5';
    } else {
      el.style.background = 'rgba(15,212,176,0.12)';
      el.style.border = '1px solid rgba(15,212,176,0.35)';
      el.style.color = '#0fd4b0';
    }
    el.textContent = message;
    document.body.appendChild(el);
    setTimeout(function () {
      el.style.transition = 'opacity 0.3s, transform 0.3s';
      el.style.opacity = '0';
      el.style.transform = 'translateX(40px)';
      setTimeout(function () { el.remove(); }, 350);
    }, 4000);
  }

  /* ── Set form loading state ────────────────────────────── */
  function setFormLoading(form, loading) {
    var btns = form.querySelectorAll('button, input[type=submit], label.topbar-btn');
    for (var i = 0; i < btns.length; i++) {
      if (loading) {
        btns[i].setAttribute('disabled', 'disabled');
        btns[i].style.pointerEvents = 'none';
        btns[i].style.opacity = '0.5';
      } else {
        btns[i].removeAttribute('disabled');
        btns[i].style.pointerEvents = '';
        btns[i].style.opacity = '';
      }
    }
  }

  /* ── Upload handler ────────────────────────────────────── */
  function getUploadFileLabel(form) {
    var fileInput = form ? form.querySelector('input[type=file]') : null;
    if (!fileInput || !fileInput.files || !fileInput.files.length) return 'Preparing upload...';
    var names = [];
    for (var i = 0; i < fileInput.files.length; i++) names.push(fileInput.files[i].name);
    var fileLabel = names.join(', ');
    return fileLabel.length > 60 ? fileLabel.substring(0, 57) + '...' : fileLabel;
  }

  function submitWithoutProgress(form) {
    if (!form || form.getAttribute('data-upload-fallback-submitted') === 'true') return;
    form.setAttribute('data-upload-fallback-submitted', 'true');
    setFormLoading(form, true);
    var overlay = createOverlay();
    updateOverlay(overlay, 'uploading', 'Uploading file...', getUploadFileLabel(form), 15);
    // Native/Vercel posts do not expose browser upload progress, but showing
    // the overlay before submit makes every upload page visibly enter an
    // uploading state until the browser navigates to the processed report.
    setTimeout(function () {
      updateOverlay(overlay, 'processing', 'Uploading file...', 'Sending file to the server...');
      HTMLFormElement.prototype.submit.call(form);
    }, 80);
  }

  function shouldUseNativeUpload() {
    var host = window.location.hostname;
    return host !== 'localhost' && host !== '127.0.0.1' && host !== '::1';
  }

  function handleUpload(form) {
    var fileInput = form.querySelector('input[type=file]');
    if (!fileInput || !fileInput.files || !fileInput.files.length) return;

    var fileLabel = getUploadFileLabel(form);

    setFormLoading(form, true);

    var overlay = createOverlay();
    updateOverlay(overlay, 'uploading', 'Uploading file...', fileLabel, 0);

    var fd = new FormData(form);

    // Ensure action=save_data is set (some forms use hidden input)
    if (!fd.has('action')) {
      var actionInput = form.querySelector('[name=action]');
      if (actionInput) fd.set('action', actionInput.value);
    }

    var xhr = new XMLHttpRequest();
    xhr.open('POST', form.action || window.location.href, true);
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

    xhr.upload.onprogress = function (e) {
      if (e.lengthComputable) {
        var pct = Math.round((e.loaded / e.total) * 100);
        updateOverlay(overlay, 'uploading', 'Uploading file...', fileLabel, pct);
      }
    };

    xhr.upload.onload = function () {
      updateOverlay(overlay, 'processing', 'Processing data...', 'Reading and validating records...');
    };

    xhr.onload = function () {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          var resp = JSON.parse(xhr.responseText);
          if (resp.ok) {
            updateOverlay(overlay, 'success', 'Upload completed', resp.message || 'Done');
            showToast(resp.message || 'Upload completed successfully', false);
            setTimeout(function () {
              removeOverlay(overlay);
              setFormLoading(form, false);
              if (resp.redirect) window.location.href = resp.redirect;
              else window.location.reload();
            }, 800);
          } else {
            updateOverlay(overlay, 'error', 'Upload failed', resp.error || 'Unknown error');
            showToast(resp.error || 'Upload failed. Please try again.', true);
            console.error('Upload error:', resp.error);
            setTimeout(function () {
              removeOverlay(overlay);
              setFormLoading(form, false);
            }, 2500);
          }
        } catch (e) {
          updateOverlay(overlay, 'processing', 'Finishing upload...', 'Reloading report page...');
          console.warn('Upload returned non-JSON response; reloading.', e);
          setTimeout(function () {
            removeOverlay(overlay);
            setFormLoading(form, false);
            window.location.href = xhr.responseURL || window.location.href;
          }, 600);
        }
      } else {
        if (xhr.status === 404 || xhr.status === 405) {
          updateOverlay(overlay, 'processing', 'Retrying upload...', 'Using standard form upload...');
          console.warn('XHR upload route returned', xhr.status, '— retrying with native form POST.');
          setTimeout(function () {
            removeOverlay(overlay);
            submitWithoutProgress(form);
          }, 500);
          return;
        }
        updateOverlay(overlay, 'error', 'Upload failed', 'Server error (' + xhr.status + ')');
        showToast('Upload failed (HTTP ' + xhr.status + '). Please try again.', true);
        console.error('HTTP error:', xhr.status, xhr.responseText);
        setTimeout(function () {
          removeOverlay(overlay);
          setFormLoading(form, false);
        }, 2500);
      }
    };

    xhr.onerror = function () {
      updateOverlay(overlay, 'error', 'Upload failed', 'Network error — check your connection');
      showToast('Network error. Please check your connection and try again.', true);
      console.error('Network error during upload');
      setTimeout(function () {
        removeOverlay(overlay);
        setFormLoading(form, false);
      }, 2500);
    };

    xhr.send(fd);
  }

  /* ── Bind all forms with data-upload-progress ──────────── */
  function bindUploadForms() {
    var forms = document.querySelectorAll('form[data-upload-progress="true"]');
    for (var i = 0; i < forms.length; i++) {
      (function (form) {
        var fileInput = form.querySelector('input[type=file]');
        if (!fileInput) return;

        if (shouldUseNativeUpload()) {
          fileInput.addEventListener('change', function () {
            if (fileInput.files && fileInput.files.length > 0) {
              // Production/Vercel upload requests are more reliable as normal
              // browser form posts than XHR multipart requests.
              submitWithoutProgress(form);
            }
          });
          return;
        }

        // Remove auto-submit onchange handlers
        fileInput.removeAttribute('onchange');

        fileInput.addEventListener('change', function () {
          if (fileInput.files && fileInput.files.length > 0) {
            handleUpload(form);
          }
        });
      })(forms[i]);
    }
  }

  /* ── Init ──────────────────────────────────────────────── */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bindUploadForms);
  } else {
    bindUploadForms();
  }
})();
