from odoo import api, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    @api.model
    def _get_assignment_fields(self):
        rule_types = self.env["crm.assignment.rule.type"].search([("active", "=", True)])
        return set(rule_types.mapped("lead_field_id.name"))

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        leads._apply_assignment_rule()
        return leads

    def write(self, vals):
        res = super().write(vals)
        if self._get_assignment_fields().intersection(vals):
            self._apply_assignment_rule()

        return res

    def _apply_assignment_rule(self):
        for lead in self:
            # Existing customer with salesperson
            if lead.partner_id and lead.partner_id.user_id:
                lead.write({"user_id": lead.partner_id.user_id.id,})
                continue
            matched_employees = self.env["hr.employee"].search([
                ("user_id", "!=", False),("company_id", "=", lead.company_id.id),])
            rules = self.env["crm.assignment.rule"].search([
                ("active", "=", True),("company_id", "=", lead.company_id.id),], order="priority, id")
            matched_rule = None
            for rule in rules:
                rule_type = rule.rule_type_id
                field_name = rule_type.lead_field_id.name
                value = lead[field_name]
                if hasattr(value, "name"):
                    value = value.name
                if not value:
                    continue
                matched_employees = self._filter_by_skill(matched_employees, rule_type.skill_type_id, value,)
                if not matched_employees:
                    break
                matched_rule = rule
            if matched_rule and matched_employees:
                lead._assign_user(matched_rule, matched_employees)

    def _filter_by_skill(self, employees, skill_type, value):
        value = str(value).strip().lower()
        return employees.filtered(
            lambda emp: any(skill.skill_type_id == skill_type and (skill.skill_id.name or "").strip().lower() == value
                for skill in emp.employee_skill_ids
            )
        )

    def _assign_user(self, rule, employees):
        self.ensure_one()
        users = employees.mapped("user_id").sorted(lambda u: u.id)
        if not users:
            return
        if len(users) == 1:
            selected_user = users[0]
        else:
            if rule.last_user_id and rule.last_user_id in users:
                current_index = users.ids.index(rule.last_user_id.id)
                next_index = (current_index + 1) % len(users)
                selected_user = users[next_index]
            else:
                selected_user = users[0]
        self.write({"user_id": selected_user.id,})
        rule.last_user_id = selected_user