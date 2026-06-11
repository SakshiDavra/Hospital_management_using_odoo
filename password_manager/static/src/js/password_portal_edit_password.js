/** @odoo-module **/

$(document).ready(function () {

    // Open Edit Password Modal
    $(document).on("click",".portal-edit-password",
        function () {
            $("#edit_password_id").val($(this).data("password-id"));
            $("#new_password").val("");
            $("#editPasswordModal").show();
        }
    );
    
    $(document).on("click","#generate_password_btn",
        function () {
            $.ajax({
                url: "/my/password/generate",
                type: "POST",
                contentType: "application/json",
                data: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: {},
                    id: Date.now(),
                }),
                success(response) {

                    console.log("Generate Response:", response);

                    const result = response.result || response;

                    if (result.password) {
                        $("#new_password").val(result.password);
                    }
                }
            });
        }
    );

    // Update Password
    $(document).on("click","#updatePasswordBtn",
        function () {
            const passwordId = $("#edit_password_id").val();
            const currentPassword = $("#current_password").val();
            const newPassword = $("#new_password").val();

            if (!currentPassword) {
                alert("Please enter current password");
                return;
            }

            if (!newPassword) {
                alert("Please enter password");
                return;
            }

            $.ajax({
                url: "/my/password/update_password",
                type: "POST",
                contentType: "application/json",

                data: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",

                    params: {
                        password_id: passwordId,
                        current_password: currentPassword,
                        new_password: newPassword,
                    },

                    id: Date.now(),
                }),

                success(response) {

                    console.log("Update Response:", response);

                    const result = response.result || response;

                    if (result.success) {

                        $("#editPasswordModal").hide();

                        alert("Password Updated Successfully");

                        location.reload();

                    } else {

                        alert(result.error || "Update Failed");
                    }
                },
                error() {
                    alert("Something went wrong");
                }
            });
        }
    );

    // Close Modal
    $(document).on("click",".close-modal",
        function () {
            $("#editPasswordModal").hide();
        }
    );

});