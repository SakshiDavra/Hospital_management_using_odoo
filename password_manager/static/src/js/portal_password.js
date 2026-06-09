/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.PasswordPortal = publicWidget.Widget.extend({
    selector: ".portal-view-password",

    events: {click: "_onViewPassword",},

    _onViewPassword(ev) {
        $("#selected_password_id").val(ev.currentTarget.dataset.passwordId);
        $("#portal_verify_password").val("");
        $("#verifyPasswordModal").show();
    },
});

$(document).ready(function () {
    $(document).on("click", ".close-modal", function () {
        $("#verifyPasswordModal, #showPasswordModal").hide();
        $("#portal_real_password").text("");
    });

    $(document).on("click", "#confirmPasswordBtn", function () {
        const passwordId = $("#selected_password_id").val();
        const loginPassword = $("#portal_verify_password").val();

        if (!loginPassword) {
            alert("Please enter password");
            return;
        }

        $.ajax({
            url: "/my/password/verify",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: {
                    password_id: passwordId,
                    login_password: loginPassword,
                },
                id: Date.now(),
            }),

            success(response) {
                const result = response.result;

                if (!result.success) {
                    alert(result.error);
                    return;
                }

                $("#verifyPasswordModal").hide();
                $("#portal_real_password").text(result.password);
                $("#showPasswordModal").show();

                let seconds = result.timeout;
                const timer = setInterval(() => {
                    seconds--;
                    if (seconds <= 0) {
                        clearInterval(timer);
                        $("#showPasswordModal").hide();
                        $("#portal_real_password").text("");
                    }
                }, 1000);
            },
            error() {
                alert("Something went wrong. Please try again.");
            },
        });
    });
});