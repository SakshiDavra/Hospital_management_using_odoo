from odoo import fields, models


class CrmAssignmentRule(models.Model):
    _name = "crm.assignment.rule"
    _description = "CRM Assignment Rule"
    _order = "sequence, id"
    name = fields.Char(required=True,)
    rule_type_id = fields.Many2one("crm.assignment.rule.type",string="Rule Type",required=True,ondelete="restrict",)
    sequence = fields.Integer(
        string="Sequence",
        default=10,
    )
    active = fields.Boolean( default=True,)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, required=True,)
    last_user_id = fields.Many2one("res.users",string="Last Assigned User", copy=False,)
    _rule_type_company_unique = models.Constraint(
        "UNIQUE(rule_type_id, company_id)",
        "Only one rule is allowed for each company.",
    )
    