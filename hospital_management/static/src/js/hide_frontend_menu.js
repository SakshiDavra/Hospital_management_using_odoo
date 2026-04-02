/** @odoo-module **/

console.log("JS LOADED ");

document.addEventListener("DOMContentLoaded", () => {
    checkPatientAndHide();
});

function checkPatientAndHide() {
    fetch('/is_patient', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
    })
    .then((res) => res.json())
    .then((data) => {
        // Odoo jsonrpc response -> { result: true/false }
        if (data && data.result === true) {
            startHiding();
        }
    })
    .catch((err) => {
        console.error("Patient check error:", err);
    });
}

function startHiding() {
    console.log("Hiding menu for patient ");

    // Continuous observer (better than blind interval)
    const observer = new MutationObserver(() => {
        removeMenuElements();
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true,
    });

    // Initial call
    removeMenuElements();
}

function removeMenuElements() {
    // Website → Backend switch button
    document.querySelectorAll('.o_frontend_to_backend_nav').forEach(el => el.remove());

    //  Dropdown menu (app list)
    document.querySelectorAll('.dropdown-menu').forEach(el => el.remove());
}