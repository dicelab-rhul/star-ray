document.addEventListener("DOMContentLoaded", function () {
    // Generate a unique token for this connection
    const uniqueToken = "token_" + new Date().getTime() + "_" + Math.random().toString(36).substring(2, 15);

    // Use the unique token in the WebSocket URL
    const ws = new WebSocket(`ws://localhost:8888/${uniqueToken}`);

    ws.onopen = function (event) {
        console.log("Connected to WebSocket with token:", uniqueToken);
        ws.send("Hello, server!");
    };

    ws.onmessage = function (event) {
        console.log("Message from server:", event.data);
    };

    ws.onclose = function (event) {
        console.log("WebSocket closed");
    };

    ws.onerror = function (error) {
        console.log("WebSocket error:", error);
    };

    // Example: Sending a message to the server every 5 seconds
    setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send("Ping");
        }
    }, 5000);
});
