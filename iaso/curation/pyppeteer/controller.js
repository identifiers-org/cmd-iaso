function (display_controller, buttons) {
    let header = document.getElementById("iaso-header");
    
    if (header === null) {
        return;
    }
    
    header = header.firstElementChild;
    
    for (const [func, title] of buttons) {
        let button = document.getElementById(`iaso-controller-${func}`);
        
        if (display_controller) {
            if (button === null) {
                button = document.createElement("button");
                button.id = `iaso-controller-${func}`;
                button.onclick = () => console.info(`iaso-controller-${func}`);
                button.innerText = title;
            }

            button.classList.remove("hidden");

            header.appendChild(button);
        } else if (button !== null) {
            button.classList.add("hidden");
        }
    }
}
