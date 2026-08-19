// Shared upload behaviour for the comparison pages.
// Two exports run to ~12 MB together and a serverless request body caps at
// 4.5 MB, so both files are gzipped in the browser before posting. Browsers
// without CompressionStream fall back to a plain post, which is fine locally.
(function () {
  var form = document.getElementById('fc-upload-form') || document.getElementById('di-upload-form');
  if (!form) return;

  function overlay(title, status) {
    var el = document.createElement('div');
    el.className = 'upload-progress-overlay visible';
    el.innerHTML =
      '<div class="upload-progress-card">' +
        '<div class="upload-progress-icon processing">' +
          '<svg viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2">' +
          '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>' +
        '</div>' +
        '<div class="upload-progress-title" data-role="title">' + title + '</div>' +
        '<div class="upload-progress-status" data-role="status">' + status + '</div>' +
        '<div class="upload-progress-bar-track"><div class="upload-progress-bar-fill indeterminate"></div></div>' +
      '</div>';
    document.body.appendChild(el);
    return {
      set: function (t, s) {
        el.querySelector('[data-role=title]').textContent = t;
        el.querySelector('[data-role=status]').textContent = s;
      },
      remove: function () { el.remove(); }
    };
  }

  function gzipFile(file) {
    var stream = file.stream().pipeThrough(new CompressionStream('gzip'));
    return new Response(stream).blob().then(function (blob) {
      return new File([blob], file.name + '.gz', { type: 'application/gzip' });
    });
  }

  form.addEventListener('submit', function (e) {
    var oldFile = form.querySelector('input[name=old_file]').files[0];
    var newFile = form.querySelector('input[name=new_file]').files[0];
    if (!oldFile || !newFile) return;          // let validation handle it

    if (typeof CompressionStream === 'undefined') {
      overlay('Comparing files...', 'Matching records on Connection No.');
      return;
    }

    e.preventDefault();
    var ui = overlay('Compressing files...', 'Shrinking the upload so the server will accept it');

    Promise.all([gzipFile(oldFile), gzipFile(newFile)]).then(function (gz) {
      ui.set('Uploading...', ((gz[0].size + gz[1].size) / 1048576).toFixed(2) + ' MB compressed from ' +
             ((oldFile.size + newFile.size) / 1048576).toFixed(2) + ' MB');
      var fd = new FormData();
      fd.append('old_file', gz[0]);
      fd.append('new_file', gz[1]);
      return fetch(form.action, {
        method: 'POST', body: fd, headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
    }).then(function (res) {
      if (res.status === 413) throw new Error('The server rejected the upload as too large even after compression.');
      return res.json().catch(function () { throw new Error('Server error (' + res.status + ')'); });
    }).then(function (data) {
      if (!data.ok) throw new Error(data.error || 'Comparison failed.');
      ui.set('Comparing...', data.message || '');
      window.location.href = data.redirect || window.location.pathname;
    }).catch(function (err) {
      ui.remove();
      alert(err.message || 'Comparison failed.');
    });
  });
})();
