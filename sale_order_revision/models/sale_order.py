from odoo import models, fields, api, _
from odoo.exceptions import UserError
from markupsafe import Markup

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    parent_order_id = fields.Many2one('sale.order', string='Original Order', copy=False)
    revision_ids = fields.One2many('sale.order', 'parent_order_id', string='Revisions')
    revision_no = fields.Integer(string='Revision No', default=0, copy=False)
    is_revision = fields.Boolean(string='Is Revision', default=False, copy=False)
    show_revision_button = fields.Boolean(compute='_compute_show_revision_button')

    @api.depends('state', 'is_revision')
    def _compute_show_revision_button(self):
        enabled = self.env['ir.config_parameter'].sudo().get_param('sale_order_revision.enable_sale_revision') == 'True'
        for rec in self:
            rec.show_revision_button = enabled and rec.state == 'sale' and not rec.is_revision

    def action_create_revision(self):
        self.ensure_one()
        if self.is_revision:
            raise UserError(_("You cannot create a revision from another revision."))

        rev_no = max(self.revision_ids.mapped('revision_no') or [0]) + 1
        new_rev = self.copy({'name': f'{self.name}-R{rev_no}', 'parent_order_id': self.id, 'revision_no': rev_no, 'is_revision': True, 'state': 'draft'})
        return {'type': 'ir.actions.act_window', 'res_model': 'sale.order', 'view_mode': 'form', 'res_id': new_rev.id, 'target': 'current'}

    def action_merge_revision(self):
        orig = self.filtered(lambda r: not r.is_revision)
        rev = self.filtered(lambda r: r.is_revision)

        if len(orig) != 1 or len(rev) != 1 or rev.parent_order_id != orig:
            raise UserError(_("Invalid selection."))

        orig_lines = orig.order_line.filtered(lambda l: not l.display_type)
        rev_lines = rev.order_line.filtered(lambda l: not l.display_type)

        for index, rev_line in enumerate(rev_lines):

            if index < len(orig_lines):
                orig_lines[index].write({
                    'product_id': rev_line.product_id.id,
                    'name': rev_line.name,
                    'product_uom_qty': rev_line.product_uom_qty,
                    'price_unit': rev_line.price_unit,
                    'tax_ids': [(6, 0, rev_line.tax_ids.ids)],
                })
            else:
                self.env['sale.order.line'].create({
                    'order_id': orig.id,
                    'product_id': rev_line.product_id.id,
                    'name': rev_line.name,
                    'product_uom_qty': rev_line.product_uom_qty,
                    'price_unit': rev_line.price_unit,
                    'tax_ids': [(6, 0, rev_line.tax_ids.ids)],
                })

        orig.message_post(body=Markup("Revision <b>%s</b> has been merged.") % rev.name)

        return {'type': 'ir.actions.client','tag': 'reload',}