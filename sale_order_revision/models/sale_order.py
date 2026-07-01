import logging
from collections import defaultdict
from itertools import zip_longest
from markupsafe import Markup

from odoo import _, api, Command, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    parent_order_id = fields.Many2one('sale.order', string='Original Order', copy=False, index=True)
    revision_ids = fields.One2many('sale.order', 'parent_order_id', string='Revisions')
    revision_no = fields.Integer(string='Revision No', default=0, copy=False)
    is_revision = fields.Boolean(string='Is Revision', default=False, copy=False)
    show_revision_button = fields.Boolean(compute='_compute_show_revision_button')
    revision_count = fields.Integer(compute="_compute_revision_count", string="Revision Count")

    _sql_constraints = [
        ('sale_revision_unique', 'unique(parent_order_id, revision_no)', 'Revision number must be unique per original order.'),
    ]

    @api.depends('revision_ids')
    def _compute_revision_count(self):
        for rec in self:
            rec.revision_count = len(rec.revision_ids)

    @api.depends('state', 'is_revision', 'company_id.enable_sale_revision')
    def _compute_show_revision_button(self):
        for rec in self:
            rec.show_revision_button = rec.company_id.enable_sale_revision and not rec.is_revision and rec.state != 'cancel'

    def action_create_revision(self):
        self.ensure_one()
        if self.is_revision:
            raise UserError(_("You cannot create a revision from another revision."))
        
        self.env.cr.execute("SELECT id FROM sale_order WHERE id = %s FOR UPDATE", (self.id,))
        rev_no = max(self.revision_ids.mapped('revision_no') or [0]) + 1
        suffix = f"{self.company_id.revision_prefix}{rev_no}" if self.company_id.revision_prefix else str(rev_no)        
        sep = self.company_id.revision_separator or '/'

        new_rev = self.copy({
            'name': f"{self.name}{sep}{suffix}", 'parent_order_id': self.id,
            'revision_no': rev_no, 'is_revision': True, 'state': 'draft',
        })

        for orig_line, rev_line in zip_longest(self.order_line.sorted('id'), new_rev.order_line.sorted('id')):
            if orig_line and rev_line:
                rev_line.parent_line_id = orig_line.id

        self.message_post(body=Markup('Revision <a href="#" data-oe-model="sale.order" data-oe-id="%s">%s</a> has been created.') % (new_rev.id, new_rev.name))
        new_rev.message_post(body=Markup('This revision was created from <a href="#" data-oe-model="sale.order" data-oe-id="%s">%s</a>.') % (self.id, self.name))
        return {'type': 'ir.actions.act_window', 'res_model': 'sale.order', 'view_mode': 'form', 'res_id': new_rev.id, 'target': 'current'}

    def action_view_revisions(self):
        self.ensure_one()
        if len(self.revision_ids) == 1:
            return {'type': 'ir.actions.act_window', 'res_model': 'sale.order', 'view_mode': 'form', 'res_id': self.revision_ids.id, 'target': 'current'}
        return {
            'type': 'ir.actions.act_window', 'name': _('Revisions'), 'res_model': 'sale.order', 'view_mode': 'list,form',
            'domain': [('id', 'in', self.revision_ids.ids)], 'target': 'current', 'context': {'create': False},
        }

    def _validate_revision_merge(self):
        if not self.is_revision or not self.parent_order_id or self.state == 'cancel':
            raise UserError(_("Invalid merge request. Verify this is an active revision with an original order."))
        return self.parent_order_id, self

    def _get_posted_invoice_map(self, orig):
        invoice_map = defaultdict(list)
        if not orig.order_line: return invoice_map
        posted_moves = self.env['account.move'].search([('invoice_origin', '=', orig.name), ('state', '=', 'posted'), ('move_type', 'in', ('out_invoice', 'out_refund'))])
        for line in posted_moves.invoice_line_ids:
            for sale_line in line.sale_line_ids:
                invoice_map[sale_line.id].append(line)
        return invoice_map

    def _prepare_adjustment(self, orig, orig_line, rev_line, price_round, posted_invoice_lines):
        qty_round = orig_line.product_uom_id.rounding

        invoice_changed = (
            float_compare(orig_line.product_uom_qty, rev_line.product_uom_qty, precision_rounding=qty_round) != 0
            or float_compare(orig_line.price_unit, rev_line.price_unit, precision_rounding=price_round) != 0
            or float_compare(orig_line.discount, rev_line.discount, precision_rounding=0.01) != 0
        )

        if not posted_invoice_lines:
            return invoice_changed, [], []

        net_posted_amount = 0.0
        net_posted_qty = 0.0

        for line in posted_invoice_lines:
            if any(sl.is_downpayment for sl in line.sale_line_ids):
                continue

            sign = 1.0 if line.move_id.move_type == 'out_invoice' else -1.0
            line_amount = (line.quantity or 0.0) * (line.price_unit or 0.0) * (1.0 - (getattr(line, 'discount', 0.0) or 0.0) / 100.0)
            net_posted_amount += sign * line_amount
            net_posted_qty += sign * (line.quantity or 0.0)

        rev_line_amount = rev_line.product_uom_qty * rev_line.price_unit * (1.0 - rev_line.discount / 100.0)
        net_amount_diff = rev_line_amount - net_posted_amount
        qty_diff = rev_line.product_uom_qty - net_posted_qty

        if float_compare(net_amount_diff, 0.0, precision_rounding=price_round) == 0 and float_compare(qty_diff, 0.0, precision_rounding=qty_round) == 0:
            return invoice_changed, [], []

        adj_qty = abs(qty_diff) if float_compare(qty_diff, 0.0, precision_rounding=qty_round) != 0 else 1.0

        adjustment_vals = {
            'product_id': rev_line.product_id.id, 'quantity': adj_qty, 'discount': 0.0,
            'name': _('%s Revision Adjustment (Posted -> Revised)') % rev_line.product_id.display_name,
            'price_unit': abs(net_amount_diff) / adj_qty if qty_diff else abs(net_amount_diff),
            'tax_ids': [Command.set(rev_line.tax_ids.ids)], 'sale_line_ids': [Command.link(orig_line.id)],
        }

        if net_amount_diff > 0:
            return invoice_changed, [Command.create(adjustment_vals)], []

        return invoice_changed, [], [Command.create(adjustment_vals)]

    def _prepare_downpayment_adjustment(self, orig, rev, price_round):
        orig_dp_lines = orig.order_line.filtered('is_downpayment')
        rev_dp_lines = rev.order_line.filtered('is_downpayment')

        if not orig_dp_lines and not rev_dp_lines:
            return False, [], []

        posted_final_invoice = self.env['account.move'].search([
            ('invoice_origin', '=', orig.name), ('state', '=', 'posted'), ('move_type', '=', 'out_invoice'), ('is_revision_adjustment', '=', False),
        ]).filtered(lambda m: any(sl and not sl.is_downpayment for line in m.invoice_line_ids for sl in line.sale_line_ids))[:1]

        if posted_final_invoice:
            return False, [], []

        new_total_without_dp = sum(l.price_total for l in rev.order_line if not l.is_downpayment)
        net_dp_paid = self._get_net_posted_downpayment(orig, orig_dp_lines) or sum(orig_dp_lines.mapped('price_unit'))

        invoice_changed = False
        positive_lines, negative_lines = [], []

        if new_total_without_dp < net_dp_paid:
            invoice_changed = True
            orig_dp_lines.write({'price_unit': new_total_without_dp})
            if rev_dp_lines:
                rev_dp_lines.write({'price_unit': new_total_without_dp})

            primary_dp = orig_dp_lines[0]
            negative_lines.append(Command.create({
                'product_id': primary_dp.product_id.id, 'quantity': 1.0, 'price_unit': net_dp_paid - new_total_without_dp,
                'name': _('Down Payment Adjustment: Refund (%s)') % rev.name, 'tax_ids': [Command.set(primary_dp.tax_ids.ids)], 'sale_line_ids': [Command.link(primary_dp.id)],
            }))
        else:
            max_allowed_dp = max(orig_dp_lines.mapped('price_unit') + [net_dp_paid])
            if float_compare(sum(orig_dp_lines.mapped('price_unit')), max_allowed_dp, precision_rounding=price_round) != 0:
                orig_dp_lines.write({'price_unit': max_allowed_dp})
                if rev_dp_lines:
                    rev_dp_lines.write({'price_unit': max_allowed_dp})
                invoice_changed = True

        return invoice_changed, positive_lines, negative_lines

    def _process_revision_lines(self, orig, rev):
        invoice_changed, positive_lines, negative_lines, new_orig_vals, rev_to_link = False, [], [], [], []
        price_round, posted_invoice_map = orig.currency_id.rounding, self._get_posted_invoice_map(orig)

        for rev_line in rev.order_line.sorted('sequence'):
            if rev_line.display_type:
                if rev_line.parent_line_id: rev_line.parent_line_id.write({'name': rev_line.name, 'sequence': rev_line.sequence})
                else:
                    new_orig_vals.append({'order_id': orig.id, 'name': rev_line.name, 'display_type': rev_line.display_type, 'sequence': rev_line.sequence})
                    rev_to_link.append(rev_line)
                continue
            if rev_line.is_downpayment: continue

            orig_line = rev_line.parent_line_id
            if orig_line:
                has_changed, pos, neg = self._prepare_adjustment(orig, orig_line, rev_line, price_round, posted_invoice_map[orig_line.id])
                if has_changed: invoice_changed = True
                positive_lines.extend(pos)
                negative_lines.extend(neg)

            vals = {'name': rev_line.name, 'sequence': rev_line.sequence, 'product_uom_qty': rev_line.product_uom_qty, 'price_unit': rev_line.price_unit, 'discount': rev_line.discount, 'tax_ids': [Command.set(rev_line.tax_ids.ids)]}
            if orig_line: orig_line.write(vals)
            else:
                new_orig_vals.append({'order_id': orig.id, 'product_id': rev_line.product_id.id, **vals})
                rev_to_link.append(rev_line)

        if new_orig_vals:
            for r_line, o_line in zip(rev_to_link, self.env['sale.order.line'].create(new_orig_vals)): r_line.parent_line_id = o_line.id

        dp_changed, dp_pos, dp_neg = self._prepare_downpayment_adjustment(orig, rev, price_round)
        if dp_changed:
            invoice_changed = True
            positive_lines.extend(dp_pos)
            negative_lines.extend(dp_neg)

        return invoice_changed, positive_lines, negative_lines

    def _update_adjustment_move(self, move, lines, message):
        if move.state != 'draft': raise UserError(_("Only draft adjustment documents can be updated."))
        move.invoice_line_ids.unlink()
        actual_lines = [Command.create(cmd[2]) for cmd in lines if cmd[0] == 0]
        if actual_lines: move.write({'invoice_line_ids': actual_lines})
        move.message_post(body=message)
        return move

    def _create_adjustment_move(self, orig, move_type, invoice_lines):
        return self.env['account.move'].create({
            'partner_id': orig.partner_id.id, 'invoice_origin': orig.name, 'invoice_date': fields.Date.today(),
            'move_type': move_type, 'is_revision_adjustment': True, 'invoice_line_ids': invoice_lines, 'company_id': orig.company_id.id,
        })

    def _handle_existing_adjustment(self, orig, rev,draft_invoice, draft_refund,positive_lines, negative_lines,):
        if draft_invoice:
            if positive_lines:
                self._update_adjustment_move(draft_invoice,positive_lines,Markup("Draft revision adjustment invoice updated for revision <b>%s</b>.") % rev.name,)
            else:
                draft_invoice.button_cancel()
                draft_invoice.message_post(body=Markup("Draft revision adjustment invoice cancelled because it is no longer required after merging revision <b>%s</b>.") % rev.name)
        elif positive_lines:
            self._create_adjustment_move(orig, "out_invoice", positive_lines)

        if draft_refund:
            if negative_lines:
                self._update_adjustment_move(draft_refund,negative_lines,Markup("Draft revision adjustment credit note updated for revision <b>%s</b>.") % rev.name,)
            else:
                draft_refund.button_cancel()
                draft_refund.message_post(body=Markup("Draft revision adjustment credit note cancelled because it is no longer required after merging revision <b>%s</b>.") % rev.name)
        elif negative_lines:
            self._create_adjustment_move(orig, "out_refund", negative_lines)

    def _get_net_posted_downpayment(self, orig, orig_dp_lines):
        if not orig_dp_lines: return 0.0
        am_lines = self.env['account.move.line'].search([('sale_line_ids', 'in', orig_dp_lines.ids), ('move_id.state', '=', 'posted'), ('move_id.move_type', 'in', ('out_invoice', 'out_refund'))])
        return sum((1.0 if aml.move_id.move_type == 'out_invoice' else -1.0) * (aml.quantity * aml.price_unit * (1.0 - (getattr(aml, 'discount', 0.0) or 0.0) / 100.0)) for aml in am_lines)

    def _update_normal_draft_invoice(self, orig, rev):
        moves = self.env['account.move'].search([('invoice_origin', '=', orig.name), ('state', '=', 'draft'), ('is_revision_adjustment', '=', False), ('move_type', 'in', ('out_invoice', 'out_refund'))])
        if not moves: return False

        rev_map = {line.parent_line_id.id: line for line in rev.order_line if line.parent_line_id}
        orig_dp_map = {line.id: line for line in orig.order_line if line.is_downpayment}

        for move in moves:
            lines_to_update = []
            for inv_line in move.invoice_line_ids:
                sale_line = inv_line.sale_line_ids[:1]
                if not sale_line: continue
                rev_line = rev_map.get(sale_line.id)
                if rev_line and not sale_line.is_downpayment:
                    lines_to_update.append(Command.update(inv_line.id, {'quantity': rev_line.product_uom_qty, 'price_unit': rev_line.price_unit, 'discount': rev_line.discount, 'tax_ids': [Command.set(rev_line.tax_ids.ids)]}))
                elif sale_line.is_downpayment and sale_line.id in orig_dp_map:
                    lines_to_update.append(Command.update(inv_line.id, {'price_unit': orig_dp_map[sale_line.id].price_unit}))
            if lines_to_update: move.write({'invoice_line_ids': lines_to_update})
        return True

    def action_merge_revision(self):
        self.ensure_one()
        orig, rev = self._validate_revision_merge()
        orig.write({'payment_term_id': rev.payment_term_id.id, 'validity_date': rev.validity_date, 'note': rev.note})        
        
        parent_line_ids = set(rev.order_line.mapped("parent_line_id").ids)
        removed_lines = orig.order_line.filtered(lambda l: l.id not in parent_line_ids)
        removed_display = removed_lines.filtered("display_type")
        if removed_display:
            rev.order_line.filtered(lambda l: l.parent_line_id.id in removed_display.ids).write({"parent_line_id": False })
            removed_display.unlink()
        (removed_lines - removed_display).write({"product_uom_qty": 0})
        
        invoice_changed, positive_lines, negative_lines = self._process_revision_lines(orig, rev)
        
        if invoice_changed:
            adjustments = self.env['account.move'].search([('invoice_origin', '=', orig.name), ('is_revision_adjustment', '=', True)])
            self._handle_existing_adjustment(orig, rev, adjustments.filtered(lambda m: m.move_type == 'out_invoice' and m.state == 'draft')[:1], adjustments.filtered(lambda m: m.move_type == 'out_refund' and m.state == 'draft')[:1], positive_lines, negative_lines)
            positive_lines = negative_lines = []

        orig.flush_recordset()
        self.env.flush_all()
        orig._compute_invoice_status()
        orig.order_line._compute_invoice_status()
        orig.order_line.filtered('is_downpayment').write({'qty_to_invoice': -1.0})
        orig.invalidate_recordset(['invoice_status'])
        orig.order_line.invalidate_recordset(['qty_to_invoice', 'invoice_status'])

        normal_draft = self.env['account.move'].search([('invoice_origin', '=', orig.name), ('state', '=', 'draft'), ('move_type', '=', 'out_invoice'), ('is_revision_adjustment', '=', False)], limit=1)
        if normal_draft: self._update_normal_draft_invoice(orig, rev)
        elif orig.invoice_status in ('to invoice', 'upselling'):
            try:
                final_inv = orig._create_invoices(final=True)
                if final_inv: orig.message_post(body=Markup('Final Invoice <a href="#" data-oe-model="account.move" data-oe-id="%s">%s</a> has been created automatically.') % (final_inv.id, final_inv.name or 'Draft'))
            except Exception as e: _logger.error("Auto final invoice error: %s", str(e))

        for lines, m_type in [(negative_lines, 'out_refund'), (positive_lines, 'out_invoice')]:
            if lines and not self.env['account.move'].search([('invoice_origin', '=', orig.name), ('state', '=', 'draft'), ('move_type', '=', m_type), ('is_revision_adjustment', '=', True)], limit=1):
                self._create_adjustment_move(orig, m_type, lines)

        orig.message_post(body=Markup('Revision <a href="#" data-oe-model="sale.order" data-oe-id="%s">%s</a> merged.') % (rev.id, rev.name))
        rev.message_post(body=Markup('Merged into <a href="#" data-oe-model="sale.order" data-oe-id="%s">%s</a>.') % (orig.id, orig.name))
        if rev.state != 'cancel': rev.action_cancel()
        
        for revision in orig.revision_ids.filtered(lambda r: r.id != rev.id and r.state != 'cancel'):
            revision.action_cancel()
            revision.message_post(body=Markup("Cancelled because <b>%s</b> was merged.") % rev.name)

        return {'type': 'ir.actions.client', 'tag': 'reload'}