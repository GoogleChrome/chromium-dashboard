/* eslint-env browser */
(function() {
  'use strict';

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js')
      .catch(function(e) {
        console.error('Error during service worker registration:', e);
      });
  }
})();
