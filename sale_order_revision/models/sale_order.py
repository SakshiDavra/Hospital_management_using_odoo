from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError
from markupsafe import Markup
import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    parent_order_id = fields.Many2one('sale.order', string='Original Order', copy=False)
    revision_ids = fields.One2many('sale.order', 'parent_order_id', string='Revisions')
    revision_no = fields.Integer(string='Revision No', default=0, copy=False)
    is_revision = fields.Boolean(string='Is Revision', default=False, copy=False)
    show_revision_button = fields.Boolean(compute='_compute_show_revision_button')
    revision_count = fields.Integer(compute="_compute_revision_count", string="Revision Count")

    @api.depends('revision_ids')
    def _compute_revision_count(self):
        for rec in self:
            rec.revision_count = len(rec.revision_ids)

    @api.depends('state', 'is_revision', 'company_id')
    def _compute_show_revision_button(self):
        for rec in self:
            rec.show_revision_button = (rec.company_id.enable_sale_revision and not rec.is_revision and rec.state != 'cancel')

    def action_create_revision(self):
        self.ensure_one()
        if self.is_revision:
            raise UserError(_("You cannot create a revision from another revision."))

        rev_no = max(self.revision_ids.mapped('revision_no') or [0]) + 1
        revision_suffix = f"{self.company_id.revision_prefix}{rev_no}" if self.company_id.revision_prefix else str(rev_no)        
        new_rev = self.copy({
            'name': f"{self.name}{self.company_id.revision_separator or '/'}{revision_suffix}",
            'parent_order_id': self.id,
            'revision_no': rev_no,
            'is_revision': True,
            'state': 'draft',
        })

        for orig_line, rev_line in zip(self.order_line.sorted('sequence'), new_rev.order_line.sorted('sequence')):
            rev_line.parent_line_id = orig_line.id

        self.message_post(
            body=Markup('Revision <a href="#" data-oe-model="sale.order" data-oe-id="%s">%s</a> has been created.') 
            % (new_rev.id, new_rev.name))
        new_rev.message_post(
            body=Markup('This revision was created from <a href="#" data-oe-model="sale.order" data-oe-id="%s">%s</a>.') 
            % (self.id, self.name))

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': new_rev.id,
            'target': 'current',
        }

    def action_merge_revision(self):
        self.ensure_one()
        orig, rev = self._validate_revision_merge()
        orig.write({'payment_term_id': rev.payment_term_id.id,'validity_date': rev.validity_date,'note': rev.note,})
        parent_line_ids = set(rev.order_line.mapped('parent_line_id').ids)
        removed_lines = orig.order_line.filtered(lambda l: l.id not in parent_line_ids)
        section_note_lines = removed_lines.filtered('display_type')
        section_note_lines.unlink()
        (removed_lines - section_note_lines).write({'product_uom_qty': 0})
        price_changed, positive_lines, negative_lines = self._process_revision_lines(orig, rev)

        if price_changed:
            self._handle_price_change_invoices(orig,rev,positive_lines,negative_lines,)

        orig.message_post(body=Markup('Revision <a href="#" data-oe-model="sale.order" '
                'data-oe-id="%s">%s</a> has been merged.') % (rev.id, rev.name))

        rev.message_post(body=Markup('Revision has been merged into ''<a href="#" data-oe-model="sale.order" '
                'data-oe-id="%s">%s</a>.') % (orig.id, orig.name))

        if rev.state != 'cancel':
            rev.action_cancel()

        for revision in orig.revision_ids.filtered(lambda r: r.id != rev.id and r.state != 'cancel'):
            revision.action_cancel()
            revision.message_post(body=Markup("Revision cancelled because revision <b>%s</b> ""was merged.") % rev.name)

        return {'type': 'ir.actions.client','tag': 'reload',}

    def action_view_revisions(self):
        self.ensure_one()
        if len(self.revision_ids) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'view_mode': 'form',
                'res_id': self.revision_ids.id,
                'target': 'current',
            }

        return {
            'type': 'ir.actions.act_window',
            'name': _('Revisions'),
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.revision_ids.ids)],
            'target': 'current',
            'context': {'create': False},
        }

    def _validate_revision_merge(self):
        if not self.is_revision:
            raise UserError(_("Only revision orders can be merged."))
        if not self.parent_order_id:
            raise UserError(_("Original order not found."))
        if self.state == 'cancel':
            raise UserError(_("Cancelled revisions cannot be merged."))
        return self.parent_order_id, self


    def _process_revision_lines(self, orig, rev):
        price_changed = False
        positive_lines, negative_lines = [], []

        for rev_line in rev.order_line.sorted('sequence'):
            orig_line = rev_line.parent_line_id

            if rev_line.display_type:
                vals = {'name': rev_line.name, 'display_type': rev_line.display_type, 'sequence': rev_line.sequence}
                if orig_line:
                    orig_line.write(vals)
                else:
                    rev_line.parent_line_id = self.env['sale.order.line'].create({'order_id': orig.id, **vals}).id
                continue

            if orig_line:
                if (float_compare(orig_line.price_unit, rev_line.price_unit, precision_rounding=orig.currency_id.rounding) != 0
                    or float_compare(orig_line.discount, rev_line.discount, precision_rounding=0.01) != 0):
                    price_changed = True

                if orig_line.qty_invoiced:

                    old_price = orig_line.price_unit * (100 - (orig_line.discount or 0.0)) / 100
                    new_price = rev_line.price_unit * (100 - (rev_line.discount or 0.0)) / 100

                    price_diff = new_price - old_price

                    if float_compare(price_diff, 0.0, precision_rounding=orig.currency_id.rounding) != 0:

                        line_vals = {
                            'product_id': rev_line.product_id.id,
                            'name': _('%s Revision Adjustment') % rev_line.product_id.display_name,
                            'quantity': orig_line.qty_invoiced,
                            'tax_ids': [(6, 0, rev_line.tax_ids.ids)],
                            'revision_sale_line_id': orig_line.id,
                            'revision_base_price': orig_line.price_unit,
                            'revision_base_qty': orig_line.qty_invoiced,
                        }

                        if price_diff > 0:
                            line_vals['price_unit'] = price_diff
                            positive_lines.append((0, 0, line_vals))

                        else:
                            line_vals['price_unit'] = abs(price_diff)
                            negative_lines.append((0, 0, line_vals))

            vals = {
                'name': rev_line.name,
                'sequence': rev_line.sequence,
                'product_uom_qty': rev_line.product_uom_qty,
                'price_unit': rev_line.price_unit,
                'discount': rev_line.discount,
                'tax_ids': [(6, 0, rev_line.tax_ids.ids)],
            }

            if orig_line:
                orig_line.write(vals)
            else:
                rev_line.parent_line_id = self.env['sale.order.line'].create({'order_id': orig.id,'product_id': rev_line.product_id.id,**vals,}).id

        return price_changed, positive_lines, negative_lines


    def _handle_price_change_invoices(self, orig, rev, positive_lines, negative_lines):
        draft_invoice = self.env['account.move'].search([
            ('invoice_origin', '=', orig.name),
            ('is_revision_adjustment', '=', True),
            ('state', '=', 'draft'),
            ('move_type', '=', 'out_invoice'),
        ], limit=1)

        if draft_invoice and positive_lines:
            draft_invoice.invoice_line_ids.unlink()
            draft_invoice.write({'invoice_line_ids': positive_lines,})

            draft_invoice.message_post(body=Markup(
                "Draft adjustment invoice updated automatically because revision <b>%s</b> changed prices.") % rev.name)

        draft_refund = self.env['account.move'].search([
            ('invoice_origin', '=', orig.name),
            ('is_revision_adjustment', '=', True),
            ('state', '=', 'draft'),
            ('move_type', '=', 'out_refund'),
        ], limit=1)

        if draft_refund and negative_lines:
            draft_refund.invoice_line_ids.unlink()
            draft_refund.write({'invoice_line_ids': negative_lines,})

            draft_refund.message_post(body=Markup(
                "Draft credit note updated automatically because revision <b>%s</b> changed prices.") % rev.name)
        if draft_invoice or draft_refund:
            return
        normal_draft_moves = self.env['account.move'].search([
            ('invoice_origin', '=', orig.name),
            ('state', '=', 'draft'),
            ('is_revision_adjustment', '=', False),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
        ])

        if normal_draft_moves:
            for move in normal_draft_moves:
                for inv_line in move.invoice_line_ids.filtered(lambda l: l.sale_line_ids):
                    sale_line = inv_line.sale_line_ids[:1]
                    rev_line = rev.order_line.filtered(lambda l: l.parent_line_id.id == sale_line.id)[:1]
                    if not rev_line:
                        continue

                    inv_line.write({
                        'price_unit': rev_line.price_unit,
                        'discount': rev_line.discount,
                        'tax_ids': [(6, 0, rev_line.tax_ids.ids)],
                    })
            return

        posted_moves = self.env['account.move'].search([
            ('invoice_origin', '=', orig.name),
            ('state', '=', 'posted'),
            ('move_type', '=', 'out_invoice'),
        ], limit=1)

        if not posted_moves:
            return
        inv_vals = {
            'partner_id': orig.partner_id.id,
            'invoice_origin': orig.name,
            'invoice_date': fields.Date.today(),
            'is_revision_adjustment': True,
        }
        if positive_lines and not draft_invoice:
            self.env['account.move'].create({**inv_vals,'move_type': 'out_invoice','invoice_line_ids': positive_lines,})

        if negative_lines and not draft_refund:
            self.env['account.move'].create({**inv_vals,'move_type': 'out_refund', 'invoice_line_ids': negative_lines,})