/* eslint max-nested-callbacks: ["error", 7] */
/* eslint-env browser */

(function(exports) {
  'use strict';

  const Toast = document.querySelector('chromedash-toast');

  let toastReady = new Promise(function(resolve, reject) {
    // If the page is using async imports, wait for them to load so toast custom
    // element is upgraded and has its methods.
    if (window.asyncImportsLoadPromise) {
      return window.asyncImportsLoadPromise.then(resolve, reject);
    }
    resolve();
  });

  /**
   * Returns a promise for the total size of assets precached by service worker.
   * @return {Promise} Promises that fulfills with the total size.
   */
  function precachedAssetTotalSize() {
    // Note that any opaque (i.e. cross-domain, without CORS) responses in the
    // cache will return a size of 0.
    return caches.keys().then(cacheNames => {
      let total = 0;

      return Promise.all(
        cacheNames.map(cacheName => {
          // Filter for assets cached by precache.
          if (!cacheName.includes('sw-precache')) {
            // eslint-disable-next-line array-callback-return
            return;
          }

          return caches.open(cacheName).then(cache => {
            return cache.keys().then(keys => {
              return Promise.all(
                keys.map(key => {
                  return cache.match(key)
                    .then(response => response.arrayBuffer())
                    .then(function(buffer) {
                      total += buffer.byteLength;
                    });
                })
              );
            });
          });
        })
      ).then(function() {
        return total;
      }).catch(function() {
        // noop!
      });
    });
  }

  /**
   * Registers a service worker.
   */
  function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/service-worker.js').then(reg => {
        reg.onupdatefound = function() {
          // The updatefound event implies that registration.installing is set.
          const installingWorker = reg.installing;
          installingWorker.onstatechange = function() {
            switch (installingWorker.state) {
              case 'installed':
                if (!navigator.serviceWorker.controller) {
                  if (Toast) {
                    toastReady.then(precachedAssetTotalSize().then(bytes => {
                      let kb = Math.round(bytes / 1000);
                      console.info('[ServiceWorker] precached', kb, 'KB');

                      // Send precached bytes to GA.
                      let metric = new Metric('sw_precache');
                      metric.sendToAnalytics(
                          'service worker', 'precache size', bytes);

                      Toast.showMessage(
                          `This site is cached (${kb}KB). ` +
                          'Ready to use offline!');
                    }));
                  }
                }
                break;
              case 'redundant':
                throw Error('The installing service worker became redundant.');
              default:
                break;
            }
          };
        };
      }).catch(function(e) {
        console.error('Error during service worker registration:', e);
      });
    }
  }

  if (!window.asyncImportsLoadPromise) {
    registerServiceWorker();
  }

  // Check to see if the service worker controlling the page at initial load
  // has become redundant, since this implies there's a new service worker with =
  // fresh content.
  if (navigator.serviceWorker && navigator.serviceWorker.controller) {
    navigator.serviceWorker.controller.onstatechange = function(e) {
      if (e.target.state === 'redundant') {
        const tapHandler = function() {
          window.location.reload();
        };

        if (Toast) {
          toastReady.then(function() {
            Toast.showMessage('A new version of this app is available.',
                              'Refresh', tapHandler, -1);
          });
        } else {
          tapHandler(); // Force reload if toast never loads.
        }
      }
    };
  }

  exports.registerServiceWorker = registerServiceWorker;
})(window);
