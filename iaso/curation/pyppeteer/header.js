function () {
    let header = document.getElementById("iaso-header");
    
    if (header !== null) {
        return true;
    }
    
    if (document.body === null) {
        return;
    }
    
    header = document.createElement("div");
    header.id = "iaso-header";

    header.innerHTML = "<div></div>";

    if (document.body.childElementCount > 0) {
        document.body.insertBefore(header, document.body.firstElementChild);
    } else {
        document.body.appendChild(header);
    }
}
