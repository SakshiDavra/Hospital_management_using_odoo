from odoo import models, fields
from datetime import datetime


class AppointmentSummaryReport(models.AbstractModel):
    _name = 'report.hospital_management.appointment_summary_template'
    _description = 'Appointment Summary Report'

    def _get_report_values(self, docids, data=None):

        docs = self.env['hospital.appointment'].sudo().browse(data['ids'])

        generated_time = fields.Datetime.context_timestamp(self, datetime.now())

        return {
            'docs': docs,
            'generated_on': generated_time
        }