from odoo import models, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class MailFollowers(models.Model):
    _inherit = 'mail.followers'

    def _insert_followers(self, res_model, res_ids, partner_ids,subtypes=None, customer_ids=None,
            check_existing=True, existing_policy='skip'):

        is_manual_follow = any([self.env.context.get('mail_followers_widget'),self.env.context.get('default_res_model'),
            existing_policy == 'replace',])

        if not is_manual_follow:

            config = self.env['follower.mail.config'].search([('model_id.model', '=', res_model),
                ('active', '=', True),('stop_auto_follower', '=', True),], limit=1)

            if config:
                if not config.filter_domain:
                    return

                domain = safe_eval(config.filter_domain)

                res_ids = [record.id
                    for record in self.env[res_model].browse(res_ids)
                    if not self.env[res_model].search([('id', '=', record.id)] + domain,limit=1)
                ]

                if not res_ids:
                    return

        return super()._insert_followers(res_model,res_ids,partner_ids,subtypes=subtypes,customer_ids=customer_ids,
            check_existing=check_existing,existing_policy=existing_policy)
    
    def _get_recipient_data(self, records, message_type, subtype_id, pids=None):
        config = self.env['follower.mail.config'].search([('model_id.model', '=', records._name), ('active', '=', True)], limit=1)
        recipient_data = super()._get_recipient_data(records, message_type, subtype_id, pids=pids)

        if not config or not config.disable_notification:
            return recipient_data

        active_lines = config.line_ids.filtered(lambda l: l.active)
        if not active_lines:
            return {record.id: {} for record in records}

        subtype_lines = active_lines.filtered(lambda l: l.subtype_id.id == subtype_id)
        if not subtype_lines:
            return recipient_data

        matched_records = records.filtered_domain(safe_eval(config.filter_domain)) if config.filter_domain else records

        block_all = any(not l.partner_ids for l in subtype_lines)
        blocked_pids = set(pid for l in subtype_lines for pid in l.partner_ids.ids)

        for record in matched_records:
            recipient_data[record.id] = {} if block_all else {
                pid: val for pid, val in recipient_data.get(record.id, {}).items() if pid not in blocked_pids
            }

        return recipient_data
    

    def write(self, vals):

        if 'subtype_ids' in vals:

            for follower in self:

                config = self.env['follower.mail.config'].search([('model_id.model', '=', follower.res_model),
                    ('active', '=', True),('disable_notification', '=', True),], limit=1)

                if not config:
                    continue

                for line in config.line_ids.filtered('active'):

                    if follower.partner_id not in line.partner_ids:
                        continue

                    for command in vals['subtype_ids']:

                        if (command[0] == 4 and line.subtype_id.id == command[1]):
                            raise ValidationError(
                                _('%s subtype is blocked for %s') % (line.subtype_id.name,follower.partner_id.name)
                            )

        return super().write(vals)