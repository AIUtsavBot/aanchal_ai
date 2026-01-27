
// FILE: frontend/src/services/notificationService.js

export const notificationService = {
    // Check if notifications are supported
    isSupported: () => 'Notification' in window,

    // Request permission
    requestPermission: async () => {
        if (!notificationService.isSupported()) return false;

        try {
            const permission = await Notification.requestPermission();
            return permission === 'granted';
        } catch (error) {
            console.error('Error requesting notification permission:', error);
            return false;
        }
    },

    // Send a local notification (if permission granted)
    sendLocalNotification: (title, options = {}) => {
        if (!notificationService.isSupported() || Notification.permission !== 'granted') {
            return;
        }

        try {
            new Notification(title, {
                icon: '/pwa-192x192.png',
                badge: '/pwa-192x192.png',
                vibrate: [200, 100, 200],
                ...options
            });
        } catch (error) {
            console.error('Error sending notification:', error);
        }
    },

    // Hook into API alerts (Mock implementation for now)
    subscribeToAlerts: (socket) => {
        // If we had a WebSocket connection, we would listen here
        // socket.on('alert', (data) => sendLocalNotification(data.title, data.body));
    }
};
