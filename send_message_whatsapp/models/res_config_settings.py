from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    send_message_whatsapp_using_queue = fields.Boolean(string="Use Queue", config_parameter='send_message_whatsapp.using_queue')
    send_message_whatsapp_notif_wa_size_cron_batch = fields.Integer(string="WA Batch Size", config_parameter='send_message_whatsapp.notif_wa_cron_batch_size')
    send_message_whatsapp_notif_wa_throttling = fields.Integer(string="Throttling", config_parameter='send_message_whatsapp.notif_wa_throttling')
    send_message_whatsapp_active_send_wa_cron = fields.Boolean(string="Active Cron", config_parameter='send_message_cron.active_send_wa_cron')
    send_message_whatsapp_api_send_wa = fields.Char(string="API URL", config_parameter='send_message_cron.api_send_wa')
    send_message_whatsapp_notif_wa_token = fields.Char(string="WA Token", config_parameter='notif_wa_token')
    send_message_whatsapp_notif_wa_test = fields.Boolean(string="Test Mode", config_parameter='notif_wa_test')
