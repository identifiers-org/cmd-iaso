function (display_informant, display_overlay, title_type, title_text, description, entity_index, issues) {
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
                        Curation required for <span id="iaso-informant-overlay-title-type"></span>
                        <span id="iaso-informant-overlay-title-text" style="font-weight: bold"></span>
                        <span id="iaso-informant-overlay-index" style="color: white"></span>:
                    </h3>
                    <h4 id="iaso-informant-overlay-description" style="color: white"></h4>
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
        const overlay_title_type = document.getElementById("iaso-informant-overlay-title-type");
        overlay_title_type.innerText = title_type;
        
        const overlay_title_text = document.getElementById("iaso-informant-overlay-title-text");
        overlay_title_text.innerText = title_text;

        const overlay_index = document.getElementById("iaso-informant-overlay-index");
        overlay_index.innerText = entity_index;
        
        const overlay_description = document.getElementById("iaso-informant-overlay-description");
        overlay_description.innerText = description;

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

        for (const [title, issue, level, tags] of issues) {
            const list = document.createElement('li');
            list.innerHTML = `<span style="text-decoration: underline">${title}: </span>`;

            const tags_selector = new IasoTagSelector(tags);

            const rendered_json = renderjson(issue);
            noclick(rendered_json, level);

            list.appendChild(tags_selector);
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
