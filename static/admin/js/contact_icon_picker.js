(function () {
    "use strict";

    const selector = "select.contact-icon-select";
    const svgNamespace = "http://www.w3.org/2000/svg";
    let pickerId = 0;

    function makeIcon(sprite, value) {
        const icon = document.createElementNS(svgNamespace, "svg");
        icon.setAttribute("viewBox", "0 0 24 24");
        icon.setAttribute("aria-hidden", "true");

        const use = document.createElementNS(svgNamespace, "use");
        use.setAttribute("href", sprite + "#" + encodeURIComponent(value));
        icon.appendChild(use);
        return icon;
    }

    function selectedOption(select) {
        return Array.from(select.options).find((option) => option.value === select.value)
            || select.options[0];
    }

    function setMenuPosition(trigger, menu) {
        const rect = trigger.getBoundingClientRect();
        const width = Math.min(310, window.innerWidth - 24);
        const left = Math.max(12, Math.min(rect.right - width, window.innerWidth - width - 12));
        const estimatedHeight = Math.min(menu.scrollHeight, 340);
        let top = rect.bottom + 6;

        if (top + estimatedHeight > window.innerHeight - 12 && rect.top > estimatedHeight + 12) {
            top = rect.top - estimatedHeight - 6;
        }

        menu.style.width = width + "px";
        menu.style.left = left + "px";
        menu.style.top = Math.max(12, top) + "px";
    }

    function enhanceSelect(select) {
        if (select.dataset.iconPickerEnhanced === "true") return;

        const sprite = select.dataset.iconSprite;
        if (!sprite) return;

        const wrapper = document.createElement("div");
        wrapper.className = "contact-icon-combobox";

        const trigger = document.createElement("button");
        trigger.type = "button";
        trigger.className = "contact-icon-trigger";
        trigger.setAttribute("aria-haspopup", "listbox");
        trigger.setAttribute("aria-expanded", "false");
        trigger.setAttribute("aria-label", "انتخاب آیکن اطلاعات تماس");

        const preview = document.createElement("span");
        preview.className = "contact-icon-preview";
        const currentLabel = document.createElement("span");
        currentLabel.className = "contact-icon-current-label";
        const arrow = document.createElement("span");
        arrow.className = "contact-icon-chevron";
        arrow.setAttribute("aria-hidden", "true");
        arrow.textContent = "⌄";
        trigger.append(preview, currentLabel, arrow);

        const menu = document.createElement("div");
        menu.className = "contact-icon-menu";
        menu.hidden = true;
        menu.setAttribute("role", "dialog");
        menu.setAttribute("aria-label", "فهرست آیکن‌ها");

        const search = document.createElement("input");
        search.type = "search";
        search.className = "contact-icon-search";
        search.placeholder = "جست‌وجوی آیکن…";
        search.setAttribute("aria-label", "جست‌وجوی آیکن");
        search.autocomplete = "off";

        const list = document.createElement("div");
        list.className = "contact-icon-options";
        list.id = "contact-icon-options-" + (++pickerId);
        list.setAttribute("role", "listbox");
        trigger.setAttribute("aria-controls", list.id);

        const optionButtons = [];
        Array.from(select.options).forEach((option) => {
            if (!option.value || option.disabled) return;

            const button = document.createElement("button");
            button.type = "button";
            button.className = "contact-icon-option";
            button.dataset.iconValue = option.value;
            button.dataset.searchText = option.textContent.trim().toLocaleLowerCase();
            button.setAttribute("role", "option");
            button.setAttribute("aria-selected", "false");

            const icon = makeIcon(sprite, option.value);
            const label = document.createElement("span");
            label.textContent = option.textContent.trim();
            button.append(icon, label);

            button.addEventListener("click", () => {
                if (select.disabled) return;
                select.value = option.value;
                select.dispatchEvent(new Event("change", { bubbles: true }));
                closeMenu();
                trigger.focus();
            });

            list.appendChild(button);
            optionButtons.push(button);
        });

        menu.append(search, list);
        document.body.appendChild(menu);

        function syncSelection() {
            const option = selectedOption(select);
            preview.replaceChildren(makeIcon(sprite, option && option.value ? option.value : "info"));
            currentLabel.textContent = option ? option.textContent.trim() : "انتخاب آیکن";
            trigger.title = currentLabel.textContent;
            optionButtons.forEach((button) => {
                const isSelected = button.dataset.iconValue === select.value;
                button.setAttribute("aria-selected", isSelected ? "true" : "false");
            });
        }

        function closeMenu() {
            menu.hidden = true;
            trigger.setAttribute("aria-expanded", "false");
            trigger.classList.remove("is-open");
        }

        function openMenu() {
            if (select.disabled) return;
            menu.hidden = false;
            setMenuPosition(trigger, menu);
            trigger.setAttribute("aria-expanded", "true");
            trigger.classList.add("is-open");
            search.value = "";
            optionButtons.forEach((button) => { button.hidden = false; });
            search.focus();
        }

        trigger.addEventListener("click", () => {
            if (menu.hidden) openMenu();
            else closeMenu();
        });

        search.addEventListener("input", () => {
            const query = search.value.trim().toLocaleLowerCase();
            optionButtons.forEach((button) => {
                button.hidden = !button.dataset.searchText.includes(query);
            });
        });

        search.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                closeMenu();
                trigger.focus();
            } else if (event.key === "ArrowDown") {
                event.preventDefault();
                const firstVisible = optionButtons.find((button) => !button.hidden);
                if (firstVisible) firstVisible.focus();
            }
        });

        list.addEventListener("keydown", (event) => {
            const visible = optionButtons.filter((button) => !button.hidden);
            const currentIndex = visible.indexOf(document.activeElement);
            if (event.key === "Escape") {
                closeMenu();
                trigger.focus();
            } else if (event.key === "ArrowDown" || event.key === "ArrowUp") {
                event.preventDefault();
                const offset = event.key === "ArrowDown" ? 1 : -1;
                const next = visible[Math.max(0, Math.min(visible.length - 1, currentIndex + offset))];
                if (next) next.focus();
            }
        });

        document.addEventListener("click", (event) => {
            if (!wrapper.contains(event.target) && !menu.contains(event.target)) closeMenu();
        });

        window.addEventListener("resize", () => {
            if (!menu.hidden) setMenuPosition(trigger, menu);
        });
        window.addEventListener("scroll", () => {
            if (!menu.hidden) setMenuPosition(trigger, menu);
        }, true);

        select.classList.add("contact-icon-select-enhanced");
        select.parentNode.insertBefore(wrapper, select);
        wrapper.append(trigger);
        wrapper.append(select);
        select.dataset.iconPickerEnhanced = "true";
        select.addEventListener("change", syncSelection);
        syncSelection();
    }

    function enhanceWithin(root) {
        if (root.matches && root.matches(selector)) enhanceSelect(root);
        if (root.querySelectorAll) root.querySelectorAll(selector).forEach(enhanceSelect);
    }

    function start() {
        enhanceWithin(document);
        const observer = new MutationObserver((records) => {
            records.forEach((record) => {
                record.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) enhanceWithin(node);
                });
            });
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", start, { once: true });
    } else {
        start();
    }
})();