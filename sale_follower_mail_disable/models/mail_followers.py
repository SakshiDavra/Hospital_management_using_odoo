from odoo import models
from odoo.tools.safe_eval import safe_eval


class MailFollowers(models.Model):
    _inherit = 'mail.followers'

    def _insert_followers(self,res_model,res_ids,partner_ids,subtypes=None,customer_ids=None,check_existing=True,existing_policy='skip'):

        blocked_models = self.env['follower.mail.config'].search([
            ('active', '=', True),('stop_auto_follower', '=', True)]).mapped('model_id.model')

        # manual follower add / subtype popup
        is_manual_follow = any([self.env.context.get('mail_followers_widget'),
            self.env.context.get('default_res_model'),
            existing_policy == 'replace',  
        ])

        # block only auto followers
        if (res_model in blocked_models and not is_manual_follow and not subtypes):
            return

        return super()._insert_followers(res_model,res_ids,partner_ids,subtypes=subtypes,customer_ids=customer_ids,
                                        check_existing=check_existing,existing_policy=existing_policy)
    

    def _get_recipient_data(self,records,message_type,subtype_id,pids=None):

        config = self.env['follower.mail.config'].search(
            [('model_id.model', '=', records._name),('active', '=', True)],limit=1)
        
        recipient_data = super()._get_recipient_data(records,message_type,subtype_id,pids=pids)

        if not config:
            return recipient_data

        # notification ON
        if not config.disable_notification:
            return recipient_data

        active_lines = config.line_ids.filtered(lambda l: l.active)

        # no filter domain
        if not config.filter_domain:

            for line in active_lines:
                if line.subtype_id.id != subtype_id:
                    continue

                # no follower selected → block all
                if not line.partner_ids:
                    return {
                        record_id: {}
                        for record_id in records.ids
                    }

                # selected follower only block
                blocked_partner_ids = line.partner_ids.ids

                for record in records:
                    recipient_data[record.id] = {
                        pid: values
                        for pid, values in recipient_data.get(
                            record.id,
                            {}
                        ).items()
                        if pid not in blocked_partner_ids
                    }

            return recipient_data

        # filter exists
        domain = safe_eval(config.filter_domain)

        for record in records:
            matched = self.env[records._name].search([('id', '=', record.id)] + domain,limit=1)

            if not matched:
                continue

            for line in active_lines:
                if line.subtype_id.id != subtype_id:
                    continue

                # no follower selected → block all
                if not line.partner_ids:
                    recipient_data[record.id] = {}
                    continue

                # selected follower only block
                blocked_partner_ids = line.partner_ids.ids
                recipient_data[record.id] = {
                    pid: values
                    for pid, values in recipient_data.get(
                        record.id,
                        {}
                    ).items()
                    if pid not in blocked_partner_ids
                }

        return recipient_dataz