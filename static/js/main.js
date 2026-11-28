(function () {
    var digitMap = {
        "0":"۰","1":"۱","2":"۲","3":"۳","4":"۴","5":"۵","6":"۶","7":"۷","8":"۸","9":"۹",
        "٠":"۰","١":"۱","٢":"۲","٣":"۳","٤":"۴","٥":"۵","٦":"۶","٧":"۷","٨":"۸","٩":"۹"
    };

    function localizeVisibleDigits() {
        if (!document.body || !window.NodeFilter) return;
        var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
            acceptNode: function (node) {
                if (!/[0-9٠-٩]/.test(node.nodeValue)) return NodeFilter.FILTER_REJECT;
                var parent = node.parentElement;
                if (parent && parent.closest(
                    "script, style, noscript, textarea, pre, code, [data-preserve-latin-digits]"
                )) return NodeFilter.FILTER_REJECT;
                return NodeFilter.FILTER_ACCEPT;
            }
        });
        var nodes = [];
        while (walker.nextNode()) nodes.push(walker.currentNode);
        nodes.forEach(function (node) {
            node.nodeValue = node.nodeValue.replace(/[0-9٠-٩]/g, function (digit) {
                return digitMap[digit] || digit;
            });
        });
    }

    // main.js is loaded at the end of the public page, after the content.
    localizeVisibleDigits();

    // --- تغییر تم تاریک/روشن ---
    var root = document.documentElement;
    var toggle = document.querySelector('.theme-toggle');
    if (toggle) {
        toggle.addEventListener('click', function () {
            var isDark = root.getAttribute('data-theme') === 'dark';
            if (isDark) {
                root.removeAttribute('data-theme');
                try { localStorage.setItem('theme', 'light'); } catch (e) {}
            } else {
                root.setAttribute('data-theme', 'dark');
                try { localStorage.setItem('theme', 'dark'); } catch (e) {}
            }
        });
    }

    // --- گالری رسانهٔ صفحهٔ جزئیات ---
    var gallery = document.querySelector("[data-property-gallery]");
    if (gallery) {
        var stage = gallery.querySelector("[data-gallery-stage]");
        var slides = Array.prototype.slice.call(gallery.querySelectorAll(".gallery-item"));
        var tabs = Array.prototype.slice.call(gallery.querySelectorAll(".gallery-thumb"));
        var currentCounter = gallery.querySelector("[data-gallery-current]");
        var caption = gallery.querySelector("[data-gallery-caption]");
        var previousButton = gallery.querySelector("[data-gallery-prev]");
        var nextButton = gallery.querySelector("[data-gallery-next]");
        var fullscreenButton = gallery.querySelector("[data-gallery-fullscreen]");
        var currentIndex = 0;
        var touchStartX = null;
        var prefersReducedMotion = window.matchMedia &&
            window.matchMedia("(prefers-reduced-motion: reduce)").matches;

        function persianDigits(value) {
            return String(value).replace(/[0-9]/g, function (digit) {
                return "۰۱۲۳۴۵۶۷۸۹"[Number(digit)];
            });
        }

        function pauseSlideMedia(slide) {
            if (!slide) return;
            var video = slide.querySelector("video");
            if (video && !video.paused) video.pause();

            var frame = slide.querySelector("iframe");
            if (frame && frame.contentWindow) {
                var source = frame.getAttribute("src") || "";
                try {
                    if (source.indexOf("youtube-nocookie.com") !== -1) {
                        frame.contentWindow.postMessage(
                            JSON.stringify({ event: "command", func: "pauseVideo", args: [] }),
                            "https://www.youtube-nocookie.com"
                        );
                    } else if (source.indexOf("player.vimeo.com") !== -1) {
                        frame.contentWindow.postMessage(
                            JSON.stringify({ method: "pause" }),
                            "https://player.vimeo.com"
                        );
                    }
                } catch (ignore) {}
            }
        }

        function activateSlide(index, shouldScrollThumb) {
            if (!slides.length) return;
            var nextIndex = (index + slides.length) % slides.length;
            if (nextIndex === currentIndex && slides[currentIndex].classList.contains("active")) return;

            pauseSlideMedia(slides[currentIndex]);
            currentIndex = nextIndex;
            slides.forEach(function (slide, slideIndex) {
                var active = slideIndex === currentIndex;
                slide.classList.toggle("active", active);
                slide.setAttribute("aria-hidden", active ? "false" : "true");
            });
            tabs.forEach(function (tab, tabIndex) {
                var active = tabIndex === currentIndex;
                tab.classList.toggle("active", active);
                tab.setAttribute("aria-selected", active ? "true" : "false");
                tab.setAttribute("tabindex", active ? "0" : "-1");
            });
            if (currentCounter) currentCounter.textContent = persianDigits(currentIndex + 1);

            var activeSlide = slides[currentIndex];
            if (caption) {
                caption.textContent = activeSlide.getAttribute("data-caption") ||
                    (activeSlide.getAttribute("data-kind") === "image" ? "تصویر ملک" : "ویدئوی ملک");
            }
            if (shouldScrollThumb && tabs[currentIndex]) {
                tabs[currentIndex].scrollIntoView({
                    behavior: prefersReducedMotion ? "auto" : "smooth",
                    block: "nearest",
                    inline: "nearest"
                });
            }
        }

        tabs.forEach(function (tab) {
            tab.addEventListener("click", function () {
                var targetIndex = Number(tab.getAttribute("data-target"));
                if (Number.isInteger(targetIndex)) activateSlide(targetIndex, true);
            });
        });
        if (previousButton) previousButton.addEventListener("click", function () {
            activateSlide(currentIndex - 1, true);
        });
        if (nextButton) nextButton.addEventListener("click", function () {
            activateSlide(currentIndex + 1, true);
        });

        if (stage) {
            stage.addEventListener("keydown", function (event) {
                if (event.target !== stage) return;
                if (event.key === "ArrowRight") {
                    event.preventDefault();
                    activateSlide(currentIndex - 1, true);
                } else if (event.key === "ArrowLeft") {
                    event.preventDefault();
                    activateSlide(currentIndex + 1, true);
                } else if (event.key === "Home") {
                    event.preventDefault();
                    activateSlide(0, true);
                } else if (event.key === "End") {
                    event.preventDefault();
                    activateSlide(slides.length - 1, true);
                }
            });
            stage.addEventListener("touchstart", function (event) {
                if (event.touches.length === 1) touchStartX = event.touches[0].clientX;
            }, { passive: true });
            stage.addEventListener("touchend", function (event) {
                if (touchStartX === null || !event.changedTouches.length) return;
                var difference = event.changedTouches[0].clientX - touchStartX;
                touchStartX = null;
                if (Math.abs(difference) < 48) return;
                activateSlide(difference < 0 ? currentIndex + 1 : currentIndex - 1, true);
            }, { passive: true });
        }

        if (fullscreenButton && stage) {
            if (!stage.requestFullscreen) {
                fullscreenButton.hidden = true;
            } else {
                fullscreenButton.addEventListener("click", function () {
                    if (document.fullscreenElement === stage) {
                        if (document.exitFullscreen) document.exitFullscreen();
                    } else {
                        var request = stage.requestFullscreen();
                        if (request && request.catch) request.catch(function () {});
                    }
                });
                document.addEventListener("fullscreenchange", function () {
                    var isFullscreen = document.fullscreenElement === stage;
                    fullscreenButton.setAttribute("aria-label", isFullscreen ? "خروج از تمام‌صفحه" : "نمایش تمام‌صفحه");
                    fullscreenButton.setAttribute("title", isFullscreen ? "خروج از تمام‌صفحه" : "نمایش تمام‌صفحه");
                });
            }
        }
    }
})();
