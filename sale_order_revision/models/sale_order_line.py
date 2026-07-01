from odoo import models, fields, api
class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    parent_line_id = fields.Many2one(
        "sale.order.line",
        string="Original Line",
        copy=False,
        index=True,
    )

    revision_line_ids = fields.One2many(
        "sale.order.line",
        "parent_line_id",
        string="Revision Lines",
    )
    @api.depends('invoice_lines.move_id.state', 'invoice_lines.move_id.is_revision_adjustment')
    def _compute_qty_invoiced(self):
        super()._compute_qty_invoiced()        
        for line in self:
            has_revision = line.invoice_lines.filtered(lambda l: l.move_id.is_revision_adjustment and l.move_id.state != 'cancel')
            if has_revision:
                line.qty_invoiced = line.product_uom_qty
