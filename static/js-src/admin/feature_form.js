(function() {
  'use strict';

  const fields = document.querySelectorAll('input, textarea');
  for (let i = 0; i < fields.length; ++i) {
    fields[i].addEventListener('input', (e) => {
      e.target.classList.add('interacted');
    });
  }

  // Allow editing if there was already a value specified in this
  // deprecated field.
  const timelineField = document.querySelector('#id_experiment_timeline');
  if (timelineField && timelineField.value) {
    timelineField.disabled = '';
  }


  if (document.querySelector('#cancel-button')) {
    document.querySelector('#cancel-button').addEventListener('click', (e) => {
      window.location.href = `/guide/edit/${e.currentTarget.dataset.id}`;
    });
  }

  document.addEventListener('DOMContentLoaded', function() {
    document.body.classList.remove('loading');
  });

  // Copy field SRC to DST if SRC is edited and DST was empty and
  // has not been edited.
  const COPY_ON_EDIT = [
    ['dt_milestone_desktop_start', 'dt_milestone_android_start'],
    ['dt_milestone_desktop_start', 'dt_milestone_webview_start'],
    // Don't autofill dt_milestone_ios_start because it is rare.
    ['ot_milestone_desktop_start', 'ot_milestone_android_start'],
    ['ot_milestone_desktop_end', 'ot_milestone_android_end'],
  ];

  for (let [srcId, dstId] of COPY_ON_EDIT) {
    let srcEl = document.getElementById('id_' + srcId);
    let dstEl = document.getElementById('id_' + dstId);
    if (srcEl && dstEl && srcEl.value == dstEl.value) {
      srcEl.addEventListener('input', (e) => {
        if (!dstEl.classList.contains('interacted')) {
          dstEl.value = srcEl.value;
          dstEl.classList.add('copied');
        }
      });
    }
  }
})();
