from odoo import fields, models


class CrmAssignmentRuleType(models.Model):
    _name = "crm.assignment.rule.type"
    _description = "CRM Assignment Rule Type"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True)
    lead_field_id = fields.Many2one(
        "ir.model.fields",
        string="Lead Field",
        required=True,
        domain=[
            ("model", "=", "crm.lead"),
            ("store", "=", True),
        ],
        ondelete="cascade",
    )
    skill_type_id = fields.Many2one(
        "hr.skill.type",
        string="Skill Type",
        required=True,
        ondelete="restrict",
        help="Employee Skill Type used to evaluate this rule.",
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    description = fields.Text()