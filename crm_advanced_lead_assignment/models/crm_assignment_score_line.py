from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CrmAssignmentScoreLine(models.Model):
    _name = "crm.assignment.score.line"
    _description = "CRM Assignment Score Range"
    _order = "from_score"
    rule_type_id = fields.Many2one("crm.assignment.rule.type", required=True, ondelete="cascade",)
    from_score = fields.Float(required=True)
    to_score = fields.Float(required=True)
    skill_id = fields.Many2one("hr.skill", required=True, )

    @api.constrains("from_score", "to_score")
    def _check_score_range(self):
        for line in self:
            if line.from_score > line.to_score:
                raise ValidationError("From Score cannot be greater than To Score.")

    @api.constrains("from_score", "to_score", "rule_type_id")
    def _check_overlapping_ranges(self):
        for line in self:
            overlap = self.search([("id", "!=", line.id),("rule_type_id", "=", line.rule_type_id.id),
                ("from_score", "<=", line.to_score),("to_score", ">=", line.from_score),  ], limit=1)
            if overlap:
                raise ValidationError("Score ranges cannot overlap for the same rule type.")