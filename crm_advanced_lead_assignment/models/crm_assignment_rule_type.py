from odoo import fields, models, api
from odoo.exceptions import ValidationError


class CrmAssignmentRuleType(models.Model):
    _name = "crm.assignment.rule.type"
    _description = "CRM Assignment Rule Type"
    _order = "id"

    name = fields.Char(required=True,translate=True,)

    processing_type = fields.Selection(
        [("field", "Field Match"),("description", "Description Match"),
            ("score", "Score Match"),("existing_customer", "Existing Customer"),("round_robin", "Round Robin"),],
        string="Processing Type", required=True, default="field",)
    
    lead_field_id = fields.Many2one("ir.model.fields",string="Lead Field",domain=[("model_id.model", "=",
         "crm.lead")], ondelete="cascade",)
    
    skill_type_id = fields.Many2one("hr.skill.type",string="Skill Type", ondelete="restrict",)

    match_model_id = fields.Many2one("ir.model", string="Description Match Model",
        domain=[("model","in",["product.template","res.partner.industry",],)],)
    
    score_line_ids = fields.One2many("crm.assignment.score.line","rule_type_id",string="Score Ranges",)
    active = fields.Boolean(default=True)
    description = fields.Text()

    @api.constrains("processing_type", "lead_field_id")
    def _check_lead_field(self):
        for rec in self:
            if rec.processing_type in ("field", "score", "description") and not rec.lead_field_id:
                raise ValidationError(_("Lead Field is required for Field Match, Score Match and Description Match."))