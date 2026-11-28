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

    // --- گالری صفحهٔ جزئیات ---
    var thumbs = document.querySelectorAll('.gallery-thumb');
    var items = document.querySelectorAll('.gallery-item');
    if (thumbs.length && items.length) {
        thumbs.forEach(function (btn) {
            btn.addEventListener('click', function () {
                var target = btn.getAttribute('data-target');
                items.forEach(function (el) {
                    if (el.getAttribute('data-index') === target) {
                        el.classList.add('active');
                        var video = el.querySelector('video');
                        if (video) video.currentTime = 0;
                    } else {
                        el.classList.remove('active');
                        var video = el.querySelector('video');
                        if (video && !video.paused) video.pause();
                    }
                });
                thumbs.forEach(function (item) {
                    item.classList.toggle('active', item === btn);
                });
            });
        });
    }
})();
