from odoo import models, fields

class AppointmentCancelWizard(models.TransientModel):
    _name = 'appointment.cancel.wizard'
    _description = 'Appointment Cancel Wizard'

    reason = fields.Text(string="Cancel Reason", required=True)
    appointment_id = fields.Many2one('hospital.appointment')

    def action_confirm_cancel(self):
        self.ensure_one()

        if not self.appointment_id:
            return

        appointment = self.appointment_id

        appointment.write({
            'state': 'cancel',
            'cancel_reason': self.reason
        })

        appointment.action_cancel_with_mail()

        return {'type': 'ir.actions.act_window_close'}