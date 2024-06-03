const WebSocketModule = (function () {
    let webSocketConnection; // Private
    const messageListeners = []; // Store message callbacks

    function connect(host, route) {
        let protocol = 'ws://';
        if (window.location.protocol === 'https:') {
            protocol = 'wss://';
        }
        webSocketConnection = new WebSocket(`${protocol}${host}/${route}`);
        webSocketConnection.onopen = () => console.log('WebSocket connection established');
        webSocketConnection.onerror = (error) => console.error('WebSocket Error:', error);

        // Invoke all callbacks when a message is received
        webSocketConnection.onmessage = (event) => {
            messageListeners.forEach(listener => listener(event.data));
        };
        console.log(`Socket connected: ${host} ${route}`)
    }

    function send(data) {
        if (webSocketConnection && webSocketConnection.readyState === WebSocket.OPEN) {
            const message = JSON.stringify(data);
            webSocketConnection.send(message);
        } else {
            console.error('WebSocket is not open. Message not sent.');
        }
    }

    // Add callback to the list
    function onMessage(callback) {
        messageListeners.push(callback);
    }

    return {
        connect,
        send,
        onMessage
    };
})();

export { WebSocketModule };