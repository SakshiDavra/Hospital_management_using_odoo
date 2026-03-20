odoo.define('hospital_management.appointment_js', function (require) {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {

        let isAutoChange = false;

        const spec = document.querySelector("[name='specialization_id']");
        const doctor = document.querySelector("[name='doctor_id']");
        const start = document.getElementById("start_date");
        const end = document.getElementById("end_date");
        const form = document.querySelector("form");

        // ================= SPECIALIZATION CHANGE =================
        if (spec && doctor) {
            spec.addEventListener("change", function () {

                const selected = this.value;

                for (let opt of doctor.options) {

                    const docSpec = opt.getAttribute("data-spec");
                    if (!docSpec) continue;

                    if (selected === "" || docSpec === selected) {
                        opt.disabled = false;
                        opt.hidden = false;
                    } else {
                        opt.disabled = true;
                        opt.hidden = true;
                    }
                }

                if (!isAutoChange) {
                    doctor.value = "";
                }

                isAutoChange = false;
            });
        }

        // ================= DOCTOR CHANGE =================
        if (doctor && spec) {
            doctor.addEventListener("change", function () {

                const selected = doctor.options[doctor.selectedIndex];
                const specId = selected.getAttribute("data-spec");

                if (specId) {
                    isAutoChange = true;
                    spec.value = specId;
                    spec.dispatchEvent(new Event('change'));
                }
            });
        }

        // ================= AUTO END DATE =================
        if (start && end) {
            start.addEventListener("change", function () {

                if (!start.value) return;

                let startDate = new Date(start.value);
                startDate.setMinutes(startDate.getMinutes() + 30);

                const year = startDate.getFullYear();
                const month = String(startDate.getMonth() + 1).padStart(2, '0');
                const day = String(startDate.getDate()).padStart(2, '0');
                const hours = String(startDate.getHours()).padStart(2, '0');
                const minutes = String(startDate.getMinutes()).padStart(2, '0');

                end.value = `${year}-${month}-${day}T${hours}:${minutes}`;
            });
        }

        // ================= FORM VALIDATION =================
        if (form && start) {
            form.addEventListener("submit", function(e) {

                const startDate = new Date(start.value);
                const now = new Date();

                if (!start.value) {
                    alert("Start date required!");
                    e.preventDefault();
                    return;
                }

                if (startDate < now) {
                    alert("You cannot create appointment in past!");
                    e.preventDefault();
                    return;
                }

                if (end && end.value) {

                    const endDate = new Date(end.value);

                    if (endDate <= startDate) {
                        alert("End time must be after start time!");
                        e.preventDefault();
                        return;
                    }

                    if (startDate.toDateString() !== endDate.toDateString()) {
                        alert("Start and End must be same day!");
                        e.preventDefault();
                        return;
                    }
                }

            });
        }

    });

});