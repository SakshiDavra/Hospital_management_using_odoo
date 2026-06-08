from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PasswordMergeWizard(models.TransientModel):
    _name = 'password.merge.wizard'
    _description = 'Password Merge Wizard'

    password_ids = fields.Many2many(
        'password.manager',
        string='Passwords'
    )

    destination_password_id = fields.Many2one(
        'password.manager',
        string='Destination Password',
        required=True
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        active_ids = self.env.context.get('active_ids', [])

        res['password_ids'] = [(6, 0, active_ids)]

        if active_ids:
            res['destination_password_id'] = active_ids[0]

        return res

    def action_merge(self):
        self.ensure_one()

        if len(self.password_ids) < 2:
            raise ValidationError(
                'Please select at least 2 passwords.'
            )

        master = self.destination_password_id

        duplicates = self.password_ids - master

        for duplicate in duplicates:

            master.category_ids |= duplicate.category_ids

            if not master.url:
                master.url = duplicate.url

            if not master.username:
                master.username = duplicate.username

            if not master.credential_type_id:
                master.credential_type_id = duplicate.credential_type_id

            master.notes = '\n'.join(
                filter(
                    None,
                    [
                        master.notes,
                        duplicate.notes
                    ]
                )
            )

            for access in duplicate.access_ids:
                access.copy({
                    'password_id': master.id
                })

            duplicate.active = False

        return {
            'type': 'ir.actions.act_window_close'
        }