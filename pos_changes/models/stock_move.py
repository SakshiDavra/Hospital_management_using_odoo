from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    custom_location_id = fields.Many2one(
        "stock.location",
        string="Preferred Location"
    )