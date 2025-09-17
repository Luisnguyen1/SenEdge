// Firebase Cloud Messaging Service Worker
importScripts('https://www.gstatic.com/firebasejs/9.22.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.22.0/firebase-messaging-compat.js');

// Initialize Firebase
// Cấu hình này sẽ được load từ server
firebase.initializeApp({
  apiKey: "AIzaSyA_4Gmz40FYwltk-t6GJMazjY4E_v9t-JA",
  authDomain: "iot-challenge-2025.firebaseapp.com",
  projectId: "iot-challenge-2025",
  storageBucket: "iot-challenge-2025.appspot.com",
  messagingSenderId: "1049728988575",
  appId: "1:1049728988575:web:c292236ada530366cab9aa"
});

const messaging = firebase.messaging();

// Handle messages when app is in background
messaging.onBackgroundMessage(function(payload) {
  console.log('[firebase-messaging-sw.js] Received background message ', payload);
  
  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: payload.notification.icon || '/static/icon.png',
    badge: payload.notification.badge || '/static/badge.png',
    tag: 'fcm-notification',
    renotify: true,
    requireInteraction: false,
    actions: [
      {
        action: 'open',
        title: 'Open',
        icon: '/static/open-icon.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/static/close-icon.png'
      }
    ],
    data: {
      url: "https://dashboard-sgteam.onrender.com/login"
    }
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification click
self.addEventListener('notificationclick', function(event) {
  console.log('[firebase-messaging-sw.js] Notification click received.');

  event.notification.close();

  if (event.action === 'close') {
    return;
  }

  // Open URL when clicking on notification
  const urlToOpen = event.notification.data.url || '/';
  
  event.waitUntil(
    clients.matchAll({
      type: 'window',
      includeUncontrolled: true
    }).then(function(clientList) {
      // Check if any tab has already opened this URL
      for (let i = 0; i < clientList.length; i++) {
        const client = clientList[i];
        if (client.url === urlToOpen && 'focus' in client) {
          return client.focus();
        }
      }
      
      // If no tab is open, create new tab
      if (clients.openWindow) {
        return clients.openWindow(urlToOpen);
      }
    })
  );
});

// Handle notification close
self.addEventListener('notificationclose', function(event) {
  console.log('[firebase-messaging-sw.js] Notification closed', event);
});