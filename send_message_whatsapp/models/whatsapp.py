import os
from odoo import models, fields, api
import requests
import logging

_logger = logging.getLogger(__name__)


class SendMessageWhatapp(models.Model):
    _inherit = "send_message.whatsapp"
    _rec_name = "id"
    _order = 'id desc'
    name = fields.Char()
    state = fields.Selection([
        ('pending', 'Pending'),
        ('requeue', 'Requeue'),
        ('queue', 'Queue'),
        ('sent', 'Sent'),
        ('fail', 'Fail')]
    )
    message = fields.Char("Message")
    recipient = fields.Char("recipient")
    user_id = fields.Many2one("res.users", string="User", default=lambda self: self.env.user.id)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)
    response_txt = fields.Text()

    def get_notif_whatapp_size_cron_batch(self):
        return int(self.env['ir.config_parameter'].get_param('send_message_whatsapp.notif_wa_size_cron_batch') or 10)

    def get_notif_whatapp_throttling(self):
        return int(self.env['ir.config_parameter'].get_param('send_message_whatsapp.notif_wa_throttling') or 10)

    def get_whatsapp_queue(self):
        return bool(self.env['ir.config_parameter'].get_param('send_message_whatsapp.using_queue'))

    def get_active_send_wa_cron(self):
        return self.env['ir.config_parameter'].get_param('send_message_cron.active_send_wa_cron')

    def get_whatsapp_endpoint_url(self):
        return os.getenv('SEND_MESSAGE_NOTIF_WA_ENDPOINT', None) or self.env['ir.config_parameter'].get_param('send_message_cron.api_send_wa')

    def get_notif_whatapp_token(self):
        return os.getenv('SEND_MESSAGE_NOTIF_WA_TOKEN', None) or self.env['ir.config_parameter'].get_param('notif_wa_token')

    def get_notif_whatapp_test(self):
        return os.getenv('SEND_MESSAGE_NOTIF_WA_TEST', None) or self.env['ir.config_parameter'].get_param('notif_wa_test')

    def send_message_whatsapp(self, message, recipient, ref="No Ref", send_force=False):
        whatsapp = self.create([
            {
                'message': message,
                'recipient': recipient,
                'name': ref,
                'state': 'pending'
            }
        ]
        )[0]
        if send_force:
            whatsapp._send_message_whatsapp()
        return whatsapp.id

    def _send_message_whatsapp(self):
        self.ensure_one()
        self.write({'state': 'queue'})
        try:
            result = self.post_whatsapp_message({
                'message': self.message,
                'recipient': self.recipient,
                'ref': self.name,
            })
            if result and result.get('status'):
                self.write({'response_txt': str(result)})
            else:
                self.write({'state': 'fail', 'response_txt': str(result)})
        except Exception as e:
            self.write({'state': 'fail', 'response_txt': str(e)})

    def cron_send_message_whatsapp(self):
        parameter = self.get_active_send_wa_cron()
        if parameter == 'True':
            size_cron_batch = self.get_notif_whatapp_size_cron_batch()
            whatsapps = self.search([('state', 'in', ['pending', 'requeue'])], order='id', limit=size_cron_batch)
            for wa in whatsapps:
                wa._send_message_whatsapp()

    def post_whatsapp_message(self, data_input):
        url = self.get_whatsapp_endpoint_url()
        token = self.get_notif_whatapp_token()
        test_wa = self.get_notif_whatapp_test()
        notif_whatapp_throttling = self.get_notif_whatapp_throttling()
        whatsapp_queue = self.get_whatsapp_queue()
        if data_input:
            data = dict(data_input)
            data['token'] = token
            recipient = data.get('recipient', '0')
            if test_wa and test_wa not in ["False", 'false']:
                _logger.info("Replace recipient from  %s to %s", recipient, test_wa)
                recipient = test_wa
            if recipient[:1] == '0':
                data['recipient'] = '62' + recipient[1:]
            else:
                data['recipient'] = recipient

            post_data = requests.post(url=url, json=data)
            return post_data.json()
        else:
            return {'status': False, 'message': "No Data"}
