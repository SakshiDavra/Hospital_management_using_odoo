from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError
from markupsafe import Markup

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    parent_order_id = fields.Many2one('sale.order', string='Original Order', copy=False)
    revision_ids = fields.One2many('sale.order', 'parent_order_id', string='Revisions')
    revision_no = fields.Integer(string='Revision No', default=0, copy=False)
    is_revision = fields.Boolean(string='Is Revision', default=False, copy=False)
    show_revision_button = fields.Boolean(compute='_compute_show_revision_button')
    revision_count = fields.Integer(
        compute="_compute_revision_count",
        string="Revision Count"
    )

    def _compute_revision_count(self):
        for rec in self:
            rec.revision_count = len(rec.revision_ids)

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
        self.message_post(body=Markup("Revision <b>%s</b> has been created.") % new_rev.name)
        new_rev.message_post(body=Markup("This revision was created from <b>%s</b>.") % self.name)
        return {'type': 'ir.actions.act_window', 'res_model': 'sale.order', 'view_mode': 'form', 'res_id': new_rev.id, 'target': 'current'}

    def action_merge_revision(self):
        self.ensure_one()

        if not self.is_revision:
            raise UserError(_("Only revision orders can be merged."))

        rev = self
        orig = rev.parent_order_id

        if not orig:
            raise UserError(_("Original order not found."))

        if rev.state == 'cancel':
            raise UserError(_("Cancelled revisions cannot be merged."))

        orig_lines = orig.order_line.filtered(lambda l: not l.display_type)
        rev_lines = rev.order_line.filtered(lambda l: not l.display_type)
        rev_products = rev_lines.mapped('product_id')
        removed_lines = orig_lines.filtered(lambda l: l.product_id not in rev_products)
        
        if removed_lines:
            removed_lines.write({'product_uom_qty': 0})
        price_changed = False
        for rev_line in rev_lines:
            orig_line = orig_lines.filtered(lambda l: l.product_id == rev_line.product_id)[:1]
            if orig_line and float_compare(orig_line.price_unit,rev_line.price_unit,precision_rounding=orig.currency_id.rounding) != 0:
                price_changed = True

            vals = {'name': rev_line.name,'product_uom_qty': rev_line.product_uom_qty,
                'price_unit': rev_line.price_unit,'tax_ids': [(6, 0, rev_line.tax_ids.ids)],}
            if orig_line:
                orig_line.write(vals)
            else:
                self.env['sale.order.line'].create({'order_id': orig.id,'product_id': rev_line.product_id.id,**vals,})

        if price_changed:
            draft_invoices = orig.invoice_ids.filtered(lambda m: m.state == 'draft' and m.move_type == 'out_invoice')

            for invoice in draft_invoices:
                invoice.button_cancel()
                invoice.message_post(body=Markup("Invoice cancelled automatically because revision <b>%s</b> changed product prices.") % rev.name)
                orig.message_post(body=Markup("Draft Invoice <b>%s</b> was cancelled automatically due to price change.") % (invoice.name or invoice.id))
            out_invoices = orig.invoice_ids.filtered(lambda m: m.state == 'posted' and m.move_type == 'out_invoice')
            credit_notes = orig.invoice_ids.filtered(lambda m: m.state == 'posted' and m.move_type == 'out_refund')
            net_invoiced_amount = (sum(out_invoices.mapped('amount_total')) - sum(credit_notes.mapped('amount_total')))
            difference = orig.amount_total - net_invoiced_amount
            if out_invoices and difference:
                inv_vals = {'partner_id': orig.partner_id.id,'invoice_origin': orig.name,'invoice_date': fields.Date.today(),}
                if difference < 0:
                    self.env['account.move'].create({**inv_vals,'move_type': 'out_refund',
                        'invoice_line_ids': [(0, 0, {
                            'name': _('Revision Adjustment'),
                            'quantity': 1,
                            'price_unit': abs(difference),})],
                    })

                    orig.message_post(body=Markup("Draft Credit Note created for <b>%s</b>.") % abs(difference))
                elif difference > 0:
                    self.env['account.move'].create({**inv_vals,'move_type': 'out_invoice',
                        'invoice_line_ids': [(0, 0, {
                            'name': _('Revision Adjustment'),
                            'quantity': 1,
                            'price_unit': difference,})],
                    })

                    orig.message_post(body=Markup("Draft Additional Invoice created for <b>%s</b>.") % difference)
        orig.message_post(body=Markup("Revision <b>%s</b> has been merged.") % rev.name)
        rev.message_post(body=Markup("Revision has been merged into <b>%s</b>.") % orig.name)
        if rev.state != 'cancel':
            rev.action_cancel()

        other_revisions = orig.revision_ids.filtered(lambda r: r.id != rev.id and r.state != 'cancel')
        for revision in other_revisions:
            revision.action_cancel()
            revision.message_post(body=Markup("Revision cancelled because revision <b>%s</b> was merged.") % rev.name)
        return {'type': 'ir.actions.client','tag': 'reload',}