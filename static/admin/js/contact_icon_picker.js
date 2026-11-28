(function () {
    "use strict";

    const selector = "select.contact-icon-select";
    const svgNamespace = "http://www.w3.org/2000/svg";

    function updateSelection(select, palette) {
        palette.querySelectorAll(".contact-icon-choice").forEach((button) => {
            const isSelected = button.dataset.iconValue === select.value;
            button.setAttribute("aria-pressed", isSelected ? "true" : "false");
        });
    }

    function enhanceSelect(select) {
        if (select.dataset.iconPickerEnhanced === "true") return;

        const sprite = select.dataset.iconSprite;
        if (!sprite) return;

        const palette = document.createElement("div");
        palette.className = "contact-icon-picker";
        palette.setAttribute("role", "group");
        palette.setAttribute("aria-label", "انتخاب آیکن اطلاعات تماس");

        Array.from(select.options).forEach((option) => {
            if (!option.value) return;

            const button = document.createElement("button");
            button.type = "button";
            button.className = "contact-icon-choice";
            button.dataset.iconValue = option.value;
            button.setAttribute("aria-label", "آیکن " + option.textContent.trim());
            button.title = option.textContent.trim();

            const icon = document.createElementNS(svgNamespace, "svg");
            icon.setAttribute("viewBox", "0 0 24 24");
            icon.setAttribute("aria-hidden", "true");
            const use = document.createElementNS(svgNamespace, "use");
            use.setAttribute("href", sprite + "#" + encodeURIComponent(option.value));
            icon.appendChild(use);

            const label = document.createElement("span");
            label.textContent = option.textContent.trim();

            button.append(icon, label);
            button.addEventListener("click", () => {
                if (select.disabled) return;
                select.value = option.value;
                select.dispatchEvent(new Event("change", { bubbles: true }));
                updateSelection(select, palette);
            });

            palette.appendChild(button);
        });

        if (!palette.childElementCount) return;

        select.classList.add("contact-icon-select-enhanced");
        select.insertAdjacentElement("afterend", palette);
        select.dataset.iconPickerEnhanced = "true";
        select.addEventListener("change", () => updateSelection(select, palette));
        updateSelection(select, palette);
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