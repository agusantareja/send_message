from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    send_message_email_cron_batch_size = fields.Integer(string="Email Batch Size", config_parameter='mail.session.batch.size')

    send_message_email_test_forwarding = fields.Char(string="Email Forwarding", config_parameter='send_message_cron.test_email')
