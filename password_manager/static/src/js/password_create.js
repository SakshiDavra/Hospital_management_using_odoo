/** @odoo-module **/

$(document).ready(function () {

    function togglePasswordMode() {
        if ($('#generate_password_type').is(':checked')) {
            $('#manual_password_div').addClass('d-none');
            $('#generate_password_div').removeClass('d-none');
        } else {
            $('#manual_password_div').removeClass('d-none');
            $('#generate_password_div').addClass('d-none');
        }
    }
    $('input[name="password_type"]').on('change',togglePasswordMode);
    $('#generate_password_btn').on( 'click',
        async function () {
            try {
                const response = await fetch('/my/password/generate',
                    {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json',},
                        body: JSON.stringify({})
                    }
                );
                const result = await response.json();
                if (result.result && result.result.password) {
                    $('#generated_password').val(result.result.password);
                    $('#password').val(result.result.password);
                }
            } catch (error) {

                console.error('Password generation failed',error);
            }
        }
    );
    togglePasswordMode();
});