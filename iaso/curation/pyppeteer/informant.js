function (display_informant, display_overlay, provider_name, provider_index, provider_issues) {
    let header = document.getElementById("iaso-header");
    
    if (header === null) {
        return;
    }
    
    header = header.firstElementChild;
    
    let overlay = document.getElementById("iaso-informant-overlay");
    
    function showOverlay() {
        document.getElementById('iaso-header').style.display = 'none';
        document.getElementById('iaso-informant-overlay').style.display = 'block';
        
        const scrollY = document.scrollingElement.scrollTop;
        
        document.body.style.overflow = 'hidden';
        document.body.style.height = '100vh';
        
        document.body.scrollTop = scrollY;
    }
    
    function hideOverlay() {
        document.getElementById('iaso-header').style.display = 'flex';
        document.getElementById("iaso-informant-overlay").style.display = 'none';
        
        const scrollY = document.body.scrollTop;
        
        document.body.style.overflow = 'initial';
        document.body.style.height = 'auto';
        
        document.scrollingElement.scrollTop = scrollY;
    }
    
    if (display_informant) {
        if (overlay === null) {
            overlay = document.createElement('div');
            overlay.id = "iaso-informant-overlay";

            overlay.innerHTML = `
                <div id="iaso-informant-overlay-content">
                    <h3 style="color: orange">
                        Curation required for resource provider
                        <span id="iaso-informant-overlay-provider" style="font-weight: bold"></span>
                        <span id="iaso-informant-overlay-index" style="color: white"></span>:
                    </h3>
                    <h4 style="color: white">The following issues were observed:</h4>
                    <ul id="iaso-informant-overlay-issues"></ul>
                </div>
            `;

            overlay.onclick = hideOverlay;

            document.body.insertBefore(overlay, document.body.firstElementChild);
        }
        
        if (display_overlay) {
            showOverlay();
        }
    } else if (overlay !== null) {
        hideOverlay();
    }
    
    if (display_informant) {
        const overlay_provider = document.getElementById("iaso-informant-overlay-provider");
        overlay_provider.innerText = provider_name;

        const overlay_index = document.getElementById("iaso-informant-overlay-index");
        overlay_index.innerText = provider_index;

        function noclick (element, show_depth) {
            if (element.onclick === null) {
                element.onclick = (element.classList.length > 0) ? ((e) => e.stopPropagation()) : hideOverlay;
            }

            if (element.classList.length == 0) {
                element.style.cursor = "default";
                element.style.pointerEvents = "auto";
            }
            
            if (element.childElementCount > 1 && element.firstElementChild.classList && element.firstElementChild.classList.contains("disclosure")) {
                show_depth -= 1;
            }

            for (const child of element.children) {
                noclick(child, show_depth);
            }
            
            if (element.classList.contains("disclosure") && show_depth < 0) {
                element.click();
            }
        };

        renderjson.set_show_to_level("all");

        const overlay_issues = document.getElementById("iaso-informant-overlay-issues");
        overlay_issues.innerHTML = "";

        for (const [title, issue, level] of provider_issues) {
            const list = document.createElement('li');
            list.innerHTML = `<span style="text-decoration: underline">${title}: </span>`;

            const rendered_json = renderjson(issue);
            noclick(rendered_json, level);

            list.appendChild(rendered_json);
            overlay_issues.appendChild(list);
        }
    }
    
    let button = document.getElementById("iaso-informant");
    
    if (display_informant) {
        if (button === null) {
            button = document.createElement("button");
            button.id = "iaso-informant";
            button.onclick = showOverlay;
            button.innerText = "Information";
        }

        button.classList.remove("hidden");

        if (header.firstElementChild === null) {
            header.appendChild(button);
        } else {
            header.insertBefore(button, header.firstElementChild);
        }
    } else if (button !== null) {
        button.classList.add("hidden");
    }
}
