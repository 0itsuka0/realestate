(function () {
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
                        var v = el.querySelector('video');
                        if (v) { v.currentTime = 0; }
                    } else {
                        el.classList.remove('active');
                        var v = el.querySelector('video');
                        if (v && !v.paused) { v.pause(); }
                    }
                });

                thumbs.forEach(function (b) {
                    b.classList.toggle('active', b === btn);
                });
            });
        });
    }
})();