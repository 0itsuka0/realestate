document.addEventListener('DOMContentLoaded', function () {
    var dealSelect = document.getElementById('id_deal_type');
    if (!dealSelect) return;

    var rentFieldIds = ['id_deposit', 'id_rent', 'id_is_convertible'];
    var saleFieldIds = ['id_price', 'id_price_per_meter'];

    function hideRow(id, hide) {
        var el = document.getElementById(id);
        if (!el) return;
        var row = el.closest('.form-row') || el.closest('.mb-3') || el.parentElement;
        if (row) row.style.display = hide ? 'none' : '';
    }

    function toggle() {
        var isRent = dealSelect.value === 'rent';
        rentFieldIds.forEach(function (id) { hideRow(id, !isRent); });
        saleFieldIds.forEach(function (id) { hideRow(id, isRent); });
    }

    dealSelect.addEventListener('change', toggle);
    toggle();

    // Apply semantic colors to the selected status on list and edit forms.
    var statusSelects = document.querySelectorAll('select.property-status-select');
    var statusClasses = [
        'status-active',
        'status-suspended',
        'status-sold',
        'status-cancelled'
    ];

    function updateStatusColor(select) {
        statusClasses.forEach(function (name) { select.classList.remove(name); });
        var statusClass = 'status-' + select.value;
        if (statusClasses.indexOf(statusClass) !== -1) {
            select.classList.add(statusClass);
        }
    }

    statusSelects.forEach(function (select) {
        updateStatusColor(select);
        select.addEventListener('change', function () {
            updateStatusColor(select);
        });
    });
});