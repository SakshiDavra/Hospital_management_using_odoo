from odoo import fields, models


class CrmAssignmentRule(models.Model):
    _name = "crm.assignment.rule"
    _description = "CRM Assignment Rule"
    _order = "priority, id"
    name = fields.Char(required=True,)
    rule_type_id = fields.Many2one("crm.assignment.rule.type",string="Rule Type",required=True,ondelete="restrict",)
    priority = fields.Integer(default=10, required=True, help="Lower value means higher priority.",)
    active = fields.Boolean( default=True,)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, required=True,)
    last_user_id = fields.Many2one(
        "res.users",
        string="Last Assigned User",
        copy=False,
    )
    _sql_constraints = [
        (
            "rule_type_company_unique",
            "unique(rule_type_id, company_id)",
            "Only one rule is allowed for each company.",
        ),
    ]