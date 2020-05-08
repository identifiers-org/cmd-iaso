function (displayController, FORWARD, BACKWARD, FINISH) {
    let controller = document.getElementById("iaso-controller");
    
    if (controller !== null) {
        controller.style.display = displayController ? "flex" : "none";
        
        return;
    }
    
    if (!displayController) {
        return;
    }
    
    controller = document.createElement("div");
    controller.id = "iaso-controller";

    controller.innerHTML = `
        <div>
            <button onclick="console.info('iaso-${FORWARD}')">
                Forward
            </button>
            <button onclick="console.info('iaso-${BACKWARD}')">
                Backward
            </button>
            <button onclick="console.info('iaso-${FINISH}')">
                End Session
            </button>
        </div>
    `;

    document.body.insertBefore(controller, document.body.firstElementChild);
}
