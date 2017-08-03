const SUPPORTS_NOTIFICATIONS = navigator.serviceWorker && window.Notification;

firebase.initializeApp({
  apiKey: "AIzaSyDMfRkOLG6OUTeEL_Z2ixEMDceyklm10UM",
  authDomain: "cr-status.firebaseapp.com",
  databaseURL: "https://cr-status.firebaseio.com",
  projectId: "cr-status",
  storageBucket: "cr-status.appspot.com",
  messagingSenderId: "999517574127"
});

class PushNotifier {
  constructor() {
    // document.querySelectorAll('.no-push-notifications').forEach(el => {
    //   el.classList.remove('no-push-notifications');
    //   el.disabled = false;
    // });

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

      // console.log('Token refreshed.');
      this._setTokenSentToServer(false);
      await this.sendTokenToServer(refreshedToken);
    });

    this.messaging.onMessage(payload => {
      const notification = new Notification(payload.notification.title, payload.notification);
      console.log(notification, payload);

      notification.onerror = function(e) {
        console.log(e);
      };

      notification.onclick = function(e) {
        //window.open(payload.notification.click_action, '_blank');
        window.focus();
      };
    });
  }

  static get SUPPORTS_NOTIFICATIONS() {
    return !!(navigator.serviceWorker && window.Notification);
  }

  _isTokenSentToServer() {
    return window.localStorage.getItem('pushTokenSentToServer') == 1;
  }

  _setTokenSentToServer(sent) {
    window.localStorage.setItem('pushTokenSentToServer', sent ? 1 : 0);
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
      return info.rel ? Object.keys(info.rel.topics) : [];
    });
  }
}

window.PushNotifier = PushNotifier;
window.PushNotifications = new PushNotifier();

// if (SUPPORTS_NOTIFICATIONS) {
//   // navigator.serviceWorker.ready.then(reg => {
//     // this.messaging.useServiceWorker(reg); // use site's existing sw instead of the one FB messaging registers.

//     // getToken().then(token => {
//     //   // console.log(token);
//     // });
//   // });
// }