import { WebSocketModule } from '/static/star_ray/websocket.js';

function handleKey(event, status) {
    var data = {
        event_type: "KeyEvent",
        source: 0, // TODO this should be something like the users session key
        // we should hope these are consistent across browsers + OS ...
        // TODO if we encounter problems, use a library like keycode-js? 
        key: event.key,
        keyCode: event.keyCode,
        timestamp: event.timeStamp,
        status: status
    };
    {% if debug %}
    console.log("key event:", data)
    {% endif %}
    WebSocketModule.send(data);
}

function handleKeyDown(event) {
    {% if disable_arrow_scroll %}
    if (event.key.startsWith('Arrow')) {
        event.preventDefault();
    }
    {% endif %}

    if (!event.repeat) {
        return handleKey(event, "down");
    }
    {% if send_key_hold %}
    else {
        return handleKey(event, "hold")
    }
    {% endif %}
}

function handleKeyUp(event) {
    handleKey(event, "up");
}

document.addEventListener('DOMContentLoaded', function () {
    document.addEventListener("keydown", handleKeyDown);
    document.addEventListener("keyup", handleKeyUp);
});


document.addEventListener('keydown', function (event) {
    // Check if the pressed key is an arrow key

});