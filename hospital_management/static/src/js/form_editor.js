/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

registry.category("website.form_editor_actions").add("create_appointment", {
    formFields: [

        {
            name: "patient_id",
            string: _t("Patient"),
            type: "many2one",
            relation: "res.partner",
            required: true,
            placeholder: "Select Patient",
            domain: [["role_ids.name", "=", "Patient"]],
        },

        {
            name: "specialization_id",
            string: _t("Specialization"),
            type: "many2one",
            placeholder: "Select Specialization",
            relation: "hospital.specialization",
        },

        {
            name: "doctor_id",
            string: _t("Doctor"),
            type: "many2one",
            relation: "res.partner",
            required: true,
            placeholder: "Select Doctor",
            domain: [["role_ids.name", "=", "Doctor"]],
        },

        // START DATE
        {
            name: "start_date",
            string: _t("Start Date"),
            type: "datetime",
            required: true,
            placeholder: "Select start date",
        },

        {
            name: "end_date",
            string: _t("End Date"),
            type: "datetime",
            required: true,
            placeholder: "Select end date",
        },

        {
            name: "symptoms",
            string: _t("Symptoms"),
            type: "text",
        },
    ],
});