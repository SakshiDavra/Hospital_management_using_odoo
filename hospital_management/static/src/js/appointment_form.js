/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.SpecializationDoctorFilter = publicWidget.Widget.extend({
    selector: ".s_website_form",

    events: {
        "change select[name='specialization_id']": "_onChangeSpec",
        "change select[name='doctor_id']": "_onChangeDoctor",
    },

    start() {

        // INITIAL FIX (IMPORTANT)
        setTimeout(() => {

            const selects = this.el.querySelectorAll("select");

            selects.forEach(select => {

                // already has empty option? skip
                if (!select.querySelector('option[value=""]')) {

                    let text = "Select";

                    if (select.name === "doctor_id") {
                        text = "Select Doctor";
                    } else if (select.name === "patient_id") {
                        text = "Select Patient";
                    } else if (select.name === "specialization_id") {
                        text = "Select Specialization";
                    }

                    const option = document.createElement("option");
                    option.value = "";
                    option.text = text;

                    select.insertBefore(option, select.firstChild);
                }

                // FORCE EMPTY (main fix)
                select.value = "";

            });

        }, 300);

        return this._super(...arguments);
    },

    async _onChangeSpec(ev) {

        const spec_id = ev.currentTarget.value;
        const doctorSelect = this.el.querySelector("select[name='doctor_id']");

        if (!doctorSelect) return;

        // reset dropdown
        doctorSelect.innerHTML = `<option value="">Select Doctor</option>`;

        // ALWAYS CALL API (even if empty)
        const doctors = await rpc("/get_doctors_by_specialization", {
            specialization_id: spec_id || false,
        });

        doctors.forEach(doc => {
            doctorSelect.innerHTML += `<option value="${doc.id}">${doc.name}</option>`;
        });
    },

    async _onChangeDoctor(ev) {
        const doctor_id = ev.currentTarget.value;

        if (!doctor_id) return;

        const data = await rpc("/get_doctor_specialization", {
            doctor_id: doctor_id,
        });

        const specSelect = this.el.querySelector("select[name='specialization_id']");
        if (specSelect && data.specialization_id) {
            specSelect.value = data.specialization_id;
        }
    },
});