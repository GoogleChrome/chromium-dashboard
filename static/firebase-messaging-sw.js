/* global importScripts, firebase */

importScripts('https://www.gstatic.com/firebasejs/4.1.3/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/4.1.3/firebase-messaging.js');

firebase.initializeApp({messagingSenderId: '999517574127'});

// Handle background messages.
firebase.messaging();
