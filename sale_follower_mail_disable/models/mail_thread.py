from odoo import api, models


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _message_auto_subscribe(self, updated_values, followers_existing_policy='skip'):
        
        blocked_models = self.env['follower.mail.config'].search([('active', '=', True),('auto_follower', '=', False)
        ]).mapped('model_id.model')

        # customer / salesperson auto follower stop
        if self._name in blocked_models:
            return True

        return super()._message_auto_subscribe(updated_values,followers_existing_policy)

    @api.model_create_multi
    def create(self, vals_list):

        blocked_models = self.env['follower.mail.config'].search([('active', '=', True),('auto_follower', '=', False)
        ]).mapped('model_id.model')

        # creator user auto follower stop
        if self._name in blocked_models:
            self = self.with_context(mail_create_nosubscribe=True)

        return super().create(vals_list)
    
    