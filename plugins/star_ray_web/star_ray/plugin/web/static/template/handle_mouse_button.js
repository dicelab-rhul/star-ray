import { WebSocketModule } from '/static/star_ray/websocket.js';

function handleMouseButton(event, status) {
    var elements = document.elementsFromPoint(event.clientX, event.clientY);
    var targets = elements.filter(el => el.id).map(el => el.id);
    var data = {
        event_type: "MouseButtonEvent",
        targets: targets,
        timestamp: event.timeStamp,
        status: status,
        position: { x: event.clientX, y: event.clientY },
        button: event.button,
    }
    {% if debug %}
    console.log("mouse event: ", data)
    {% endif %}
    WebSocketModule.send(data)
}

function handleMouseDown(event) {
    handleMouseButton(event, "down")
}

function handleMouseUp(event) {
    handleMouseButton(event, "up")
}

function handleMouseClick(event) {
    handleMouseButton(event, "click")
}

document.addEventListener('DOMContentLoaded', function () {
    {% if disable_context_menu %}
    window.addEventListener(`contextmenu`, (e) => e.preventDefault());
    {% endif %}
    document.addEventListener("mousedown", handleMouseDown)
    document.addEventListener("mouseup", handleMouseUp)
    document.addEventListener("click", handleMouseClick)
});