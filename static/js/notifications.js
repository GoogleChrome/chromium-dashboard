(function(exports) {
'use strict';

let _libsLoaded = false;

/**
 * Lazy loads a script.
 * @param {string} src
 * @return {!Promise}
 */
function loadLib(src) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = src;
    script.onload = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

/**
 * Lazy load the Firebase Messaging (FCM) SDK.
 */
async function loadLibs() {
  await loadLib('https://www.gstatic.com/firebasejs/4.1.3/firebase-app.js');
  await loadLib('https://www.gstatic.com/firebasejs/4.1.3/firebase-messaging.js');
  _libsLoaded = true;
}

class PushNotifier {
  init() {
    if (!_libsLoaded) {
      throw Error('Firebase SDK not loaded.');
    }

    firebase.initializeApp({
      apiKey: "AIzaSyDMfRkOLG6OUTeEL_Z2ixEMDceyklm10UM",
      authDomain: "cr-status.firebaseapp.com",
      databaseURL: "https://cr-status.firebaseio.com",
      projectId: "cr-status",
      storageBucket: "cr-status.appspot.com",
      messagingSenderId: "999517574127"
    });

    this.messaging = firebase.messaging();

    this.messaging.onTokenRefresh(async () => {
      let refreshedToken;
      try {
        // Get Instance ID token. Initially this makes a network call. Once
        // retrieved, subsequent calls to getToken will return from the cache.
        refreshedToken = await this.messaging.getToken();
      } catch (err) {
        console.error('Unable to retrieve refreshed token ', err);
        return;
      }

      this._setTokenSentToServer(false);
      await this.sendTokenToServer(refreshedToken);
    });

    this.messaging.onMessage(payload => {
      const notification = new Notification(payload.notification.title, payload.notification);

      notification.onerror = function(e) {
        console.log(e);
      };

      notification.onclick = function(e) {
        //window.open(payload.notification.click_action, '_blank');
        exports.focus();
      };
    });
  }

  static get SUPPORTS_NOTIFICATIONS() {
    return !!(navigator.serviceWorker && exports.Notification);
  }

  static get GRANTED_ACCESS() {
    return Notification.permission === 'granted';
  }

  _isTokenSentToServer() {
    return exports.localStorage.getItem('pushTokenSentToServer') == 1;
  }

  _setTokenSentToServer(sent) {
    exports.localStorage.setItem('pushTokenSentToServer', sent ? 1 : 0);
  }

  /**
   * @param {string=} token
   */
  async getTokenInfo(token = null) {
    token = token || await this.getToken();

    try {
      const resp = await fetch('/features/push/info', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({subscriptionId: token})
      });
      return await resp.json();
    } catch(err) {
      console.error('Error sending notification to FCM.', err);
    }
  }

  async requestNotifications() {
    try {
      await this.messaging.requestPermission();
    } catch (err) {
      console.error('Unable to get permission to notify.', err);
    }
    return Notification.permission === 'granted';
  }

  async getToken() {
    let currentToken;
    try {
      // Get Instance ID token. Initially this makes a network call, once retrieved
      // subsequent calls to getToken will return from cache.
      currentToken = await this.messaging.getToken();
    } catch (err) {
      console.log('An error occurred while retrieving token. ', err);
      this._setTokenSentToServer(false);
      return;
    }

    if (currentToken) {
      await this.sendTokenToServer(currentToken);
    } else {
      // console.log('No Instance ID token available. Request permission to generate one.');
      // Prompt user to enable notifications.
      this._setTokenSentToServer(false);
      const granted = await this.requestNotifications();
      if (granted) {
        currentToken = await this.getToken();
      }
    }

    return currentToken;
  }

  async sendTokenToServer(token) {
    if (!this._isTokenSentToServer()) {
      const resp = await fetch('/features/push/new', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({subscriptionId: token})
      });

      this._setTokenSentToServer(true);
      // console.log('Token sent to server.');
    }
  }

  async subscribeToFeature(featureId, remove=false) {
    const token = await this.getToken();

    try {
      const body = {subscriptionId: token};
      if (remove) {
        body.remove = true;
      }
      const resp = await fetch(`/features/push/subscribe/${featureId}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body)
      });
    } catch(err) {
      console.error('Error [un]subscribing to topic.', err);
    }

    return await this.getTokenInfo(token);
  }

  async unsubscribeFromFeature(featureId) {
    return this.subscribeToFeature(featureId, true);
  }

  async getAllSubscribedFeatures() {
    const token = await this.getToken();

    return this.getTokenInfo(token).then(info => {
      return info.rel ? Object.keys(info.rel.topics).map(id => parseInt(id)) : [];
    });
  }
}

exports.PushNotifier = PushNotifier;
exports.PushNotifications = new PushNotifier();
exports.loadFirebaseSDKLibs = loadLibs;

// if (SUPPORTS_NOTIFICATIONS) {
//   // navigator.serviceWorker.ready.then(reg => {
//     // this.messaging.useServiceWorker(reg); // use site's existing sw instead of the one FB messaging registers.

//     // getToken().then(token => {
//     //   // console.log(token);
//     // });
//   // });
// }

})(window);
