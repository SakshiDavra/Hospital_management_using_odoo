/** @odoo-module */

import { BaseOptionComponent } from "@html_builder/core/utils";
import { useService } from "@web/core/utils/hooks";
import { onWillStart } from "@odoo/owl";

export class SpecializationOption extends BaseOptionComponent {
    static template = "hospital.specialization_option";
    static selector = ".s_specialization_list_snippets";

    setup() {
        super.setup();
        this.orm = useService("orm");

        this.count = 0;

        this.preventPreview = true;

        onWillStart(async () => {
            const records = await this.orm.searchRead(
                "hospital.specialization",
                [],
                ["id"]
            );

            this.count = records.length;
        });
    }
}