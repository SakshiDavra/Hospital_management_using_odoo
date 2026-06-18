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
    revision_count = fields.Integer(compute="_compute_revision_count",string="Revision Count")
    
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

        prefix = self.env['ir.config_parameter'].sudo().get_param('sale_order_revision.revision_prefix','R')
        rev_no = max(self.revision_ids.mapped('revision_no') or [0]) + 1
        new_rev = self.copy({
            'name': f'{self.name}-{prefix}{rev_no}',
            'parent_order_id': self.id,
            'revision_no': rev_no,
            'is_revision': True,
            'state': 'draft',
        })
        orig_lines = self.order_line.filtered(lambda l: not l.display_type)
        rev_lines = new_rev.order_line.filtered(lambda l: not l.display_type)

        for orig_line, rev_line in zip(orig_lines, rev_lines):
            rev_line.parent_line_id = orig_line.id

        self.message_post(body=Markup('Revision <a href="#" data-oe-model="sale.order" data-oe-id="%s">%s</a> has been created.'
            ) % (new_rev.id, new_rev.name))

        new_rev.message_post(body=Markup('This revision was created from <a href="#" data-oe-model="sale.order" data-oe-id="%s">%s</a>.'
            ) % (self.id, self.name))

        return {'type': 'ir.actions.act_window','res_model': 'sale.order',
            'view_mode': 'form','res_id': new_rev.id,'target': 'current',}
    
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
        linked_orig_lines = rev_lines.mapped('parent_line_id')
        removed_lines = orig_lines.filtered(lambda l: l not in linked_orig_lines)

        if removed_lines:
            removed_lines.write({'product_uom_qty': 0})

        price_changed = False
        positive_lines = []
        negative_lines = []

        for rev_line in rev_lines:
            orig_line = rev_line.parent_line_id

            if orig_line:

                if (float_compare(orig_line.price_unit,rev_line.price_unit,precision_rounding=orig.currency_id.rounding) != 0
                    or
                    float_compare(orig_line.discount,rev_line.discount,precision_rounding=0.01) != 0):
                    price_changed = True

                already_invoiced_qty = orig_line.qty_invoiced

                if already_invoiced_qty:
                    old_amount = (orig_line.price_unit * already_invoiced_qty * (1 - (orig_line.discount or 0.0) / 100))
                    new_amount = (rev_line.price_unit * already_invoiced_qty * (1 - (rev_line.discount or 0.0) / 100))
                    diff = new_amount - old_amount

                    if float_compare(diff,0.0,precision_rounding=orig.currency_id.rounding) != 0:
                        if diff > 0:
                            positive_lines.append(
                                (0, 0, {
                                    'product_id': rev_line.product_id.id,
                                    'name': _('%s Revision Adjustment') % rev_line.product_id.display_name,
                                    'quantity': 1,
                                    'price_unit': diff,
                                    'tax_ids': [(6, 0, rev_line.tax_ids.ids)],
                                })
                            )

                        elif diff < 0:
                            negative_lines.append(
                                (0, 0, {
                                    'product_id': rev_line.product_id.id,
                                    'name': _('%s Revision Adjustment') % rev_line.product_id.display_name,
                                    'quantity': 1,
                                    'price_unit': abs(diff),
                                    'tax_ids': [(6, 0, rev_line.tax_ids.ids)],
                                })
                            )

            vals = {'name': rev_line.name,
                'product_uom_qty': rev_line.product_uom_qty,
                'price_unit': rev_line.price_unit,
                'discount': rev_line.discount,
                'tax_ids': [(6, 0, rev_line.tax_ids.ids)],}

            if orig_line:
                orig_line.write(vals)
            else:
                new_line = self.env['sale.order.line'].create({'order_id': orig.id,'product_id': rev_line.product_id.id,**vals,})
                rev_line.parent_line_id = new_line.id

        if price_changed:
            draft_moves = orig.invoice_ids.filtered(lambda m: m.state == 'draft'and m.move_type in ('out_invoice', 'out_refund'))

            for move in draft_moves:
                move.button_cancel()
                move.message_post(body=Markup("Invoice/Credit Note cancelled automatically because ""revision <b>%s</b> changed product prices.") % rev.name)
                orig.message_post(body=Markup("Draft document <b>%s</b> was cancelled automatically due to revision changes.") % (move.name or move.id))
            posted_moves = orig.invoice_ids.filtered(lambda m: m.state == 'posted' and m.move_type in ('out_invoice', 'out_refund'))

            if posted_moves:

                inv_vals = {'partner_id': orig.partner_id.id,'invoice_origin': orig.name,'invoice_date': fields.Date.today(),}
                if positive_lines:
                    self.env['account.move'].create({ **inv_vals,'move_type': 'out_invoice','invoice_line_ids': positive_lines,})
                    orig.message_post(body=Markup("Draft Additional Invoice created for revision price/discount changes."))

                if negative_lines:
                    self.env['account.move'].create({**inv_vals,'move_type': 'out_refund','invoice_line_ids': negative_lines,})
                    orig.message_post(body=Markup("Draft Credit Note created for revision price/discount changes."))

        orig.message_post(body=Markup('Revision <a href="#" data-oe-model="sale.order" ''data-oe-id="%s">%s</a> has been merged.') % (rev.id, rev.name))
        rev.message_post(body=Markup('Revision has been merged into ''<a href="#" data-oe-model="sale.order" ''data-oe-id="%s">%s</a>.') % (orig.id, orig.name))

        if rev.state != 'cancel':
            rev.action_cancel()

        other_revisions = orig.revision_ids.filtered(lambda r: r.id != rev.id and r.state != 'cancel')

        for revision in other_revisions:
            revision.action_cancel()
            revision.message_post(body=Markup("Revision cancelled because revision " "<b>%s</b> was merged.") % rev.name)

        return {'type': 'ir.actions.client','tag': 'reload',}
    
    def action_view_revisions(self):
        self.ensure_one()

        revisions = self.revision_ids
        if len(revisions) == 1:
            return {'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'view_mode': 'form',
                'res_id': revisions.id,
                'target': 'current',}

        return {'type': 'ir.actions.act_window',
            'name': _('Revisions'),
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', revisions.ids)],
            'target': 'current',
            'context': {'create': False,},
        }