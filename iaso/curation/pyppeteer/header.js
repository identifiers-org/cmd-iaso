function () {
    let header = document.getElementById("iaso-header");
    
    if (header !== null) {
        return;
    }
    
    header = document.createElement("div");
    header.id = "iaso-header";

    header.innerHTML = "<div></div>";

    document.body.insertBefore(header, document.body.firstElementChild);
}
