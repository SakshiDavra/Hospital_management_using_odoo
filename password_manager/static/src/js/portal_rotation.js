/** @odoo-module **/

$(document).ready(function () {

    function updateRotationDate() {
        const days = parseInt($('input[name="rotation_days"]').val() || 0);
        if (!days) {
            $('#rotation_date_preview').val('');
            return;
        }
        let today = new Date();
        today.setDate(today.getDate() + days);
        let day = String(today.getDate()).padStart(2, '0');
        let month = String(today.getMonth() + 1).padStart(2, '0');
        let year = today.getFullYear();
        $('#rotation_date_preview').val(`${day}-${month}-${year}`);
    }
    $('input[name="rotation_days"]').on('input',updateRotationDate);
    updateRotationDate();

});