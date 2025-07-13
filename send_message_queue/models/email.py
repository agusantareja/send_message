from odoo import models, fields, api
from datetime import datetime
import json
import pytz
import requests
import logging
import time

from odoo.addons.queue_job.job import job

_logger = logging.getLogger(__name__)

class SendEmail(models.Model):
    _inherit = "send_message.email"
    # _rec_name = "id"
    # _order = 'id desc'
    email_from = fields.Char("Email From")
    user_id = fields.Many2one("res.users", string="User", default=lambda self: self.env.user.id)
    is_send_email = fields.Boolean("Is Send Email", default=False)
    force_send_email = fields.Boolean("Force Send Email", default=False)

    @api.model
    def create(self, vals):
        # Override create method to set email_from if not provided
        if 'email_from' not in vals:
            vals['email_from'] = self.env.company.email or self.env.user.email
        vals['is_send'] = True
        result = super(SendEmail, self).create(vals)
        # Automatically set is_send_email to False when creating a new record
        if result.template:
            result.with_delay().send_email_queue()
        result.with_delay().send_wa_queue()
        return result

    #function ini untuk mengirim email secara otamatis yang terhubung dengan cron job

    def send_email(self):
        #jika paramater True maka function ini akan berjalan, jika False maka akan berhenti. setting paramater ini terdapat pada
        #System Paramater
        parameter = self.env['ir.config_parameter'].get_param('send_message_cron.active_send_email_cron')
        if parameter == 'True':
            for rec in self.env['send_message.email'].search([('is_send', '=', False)]):
                if not rec.is_send_email:
                    rec.with_delay().send_email_queue()
                if not rec.is_send_wa:
                    rec.with_delay().send_wa_queue()
    @job
    def send_email_queue(self):
        parameter = self.env['ir.config_parameter'].get_param('send_message_cron.active_send_email_cron')
        if parameter == 'True' and not self.is_send_email:
            send = self # .env['send_message.email'].search([('is_send', '=', False)], limit=3)
            log = self.env['send_message.log']
            now = datetime.now(pytz.timezone('Asia/Jakarta'))
            date_time = now.strftime("%d/%m/%Y %H:%M:%S")
            message = {}
            #looping dahulu data yang ada di tabel
            test_email = self.env['ir.config_parameter'].get_param('send_message_cron.test_email')
            for record in send:
                template = record.template
                if not template:
                    message["name"] = date_time
                    message["message"] = "Something wrong when send email please check log"
                    record.write({'is_send_email': True})
                    log.create(message)
                    self._cr.commit()
                    self.failed_send_mail_message(self.id, "email")
                    self.failed_send_wa_message("email")
                    continue
                template_values = {
                    'email_from': record.email_from or record.company_id.email or record.user_id.email,
                    'auto_delete': True
                }
                if test_email != 'False':
                    template_values['email_to'] = test_email
                elif record.receiver:
                    email = record.receiver.partner_id.email
                    if email:
                        template_values['email_to'] = email
                    else:
                        message["name"] = date_time
                        message["message"] = "Failed no email for %s"%(record.receiver.name)
                        log.create(message)
                        record.write({'is_send_email': True})
                        self._cr.commit()
                        continue
                else:
                    email_ex = record.email_ex
                    if email_ex:
                        template_values['email_to'] = email_ex
                try:
                    mail_template = template.with_user(record.user_id).send_mail(
                        record.id_record,
                        email_values=template_values,
                        force_send=record.force_send_email
                    )
                    message["name"] = date_time
                    message["message"] = "Success to send email %s" % (mail_template)
                except Exception as e:
                    message["name"] = date_time
                    message["message"] = "Something wrong when send email please check log"
                    _logger.error("Error sending email: %s", e)
                    record.write({'is_send_email': True})
                    self._cr.commit()
                    self.failed_send_mail_message(self.id, "email")
                    self.failed_send_wa_message("email")
                log.create(message)

    #function ini untuk send wa cron job
    @job
    def send_wa_queue(self):
        parameter = self.env['ir.config_parameter'].get_param('send_message_cron.active_send_wa_cron')
        if parameter == 'True':
            data_send = self
            test_wa = self.env['ir.config_parameter'].get_param('notif_wa_test')
            for record in data_send:
                data = {
                    'message': record.message,
                    'ref': record.ref
                }
                no_wa = self.env['hr.employee'].search([('user_id', '=', record.receiver.id)], limit=1)
                if test_wa != 'False':
                    data['recipient'] = test_wa
                elif no_wa.mobile_phone:
                    data['recipient'] = no_wa.mobile_phone
                elif record.contact_ex:
                    data['recipient'] = record.receiver_ex
                else:
                    record.write({'is_send_wa': True})
                    self._cr.commit()
                    self.failed_send_mail_message(self.id, "wa")
                    self.failed_send_wa_message("wa")
                    continue

                try:
                    response_content = self.post_wa_message(data)
                    if response_content['status'] == True:
                        record.write({'response': 'success'})
                    else:
                        record.write({'response': 'failed'})
                    record.write({'is_send_wa': True})
                    self._cr.commit()
                except Exception:
                    record.write({'response': 'something wrong please check log'})
                    record.write({'is_send_wa': True})
                    self._cr.commit()
                    self.failed_send_mail_message(self.id, "wa")
                    self.failed_send_wa_message("wa")

    def post_wa_message(self, data_input):
        url = self.env['ir.config_parameter'].get_param('send_message_cron.api_send_wa')
        token = self.env['ir.config_parameter'].get_param('notif_wa_token')
        if data_input:
            data = dict(data_input)
            data['token'] = token
            recipient = data.get('recipient', '0')
            if recipient[:1] == '0':
                data['recipient'] ='62' + recipient[1:]
            post_data = requests.post(url=url, json=data)
            return post_data.json()
        else:
            return {'status': False, 'message': "No Data"}

    def _send_mail_message(self, template_email, template_values):
        email_values = {
            'email_from': self.company_id.email or self.env.company.email,
            'auto_delete': True,
        }
        if template_values:
            email_values.update(template_values)
        mail_template = template_email.with_user(self.user_id).send_mail(
            self.id_record,
            email_values=email_values,
            force_send=self.force_send_email
        )
        now = datetime.now(pytz.timezone('Asia/Jakarta'))
        date_time = now.strftime("%d/%m/%Y %H:%M:%S")
        message = {
            "name": date_time,
            "message": "Success to send email %s" % (mail_template)
        }
        self.env['send_message.log'].create(message)

    def _failed_send_mail_message(self, type: str):
        template_email = ""
        if type == "email":
            template_email = self.env.ref('send_message_cron.failed_send_mail_template')
        else:
            template_email = self.env.ref('send_message_cron.failed_send_wa_template')
        groups = self.env.ref('send_message_cron.group_failed_notif_receiver')
        record = self
        for user in groups.users:
            template_values = {
                'email_from': self.env.company.email,
                'email_to': user.partner_id.email,
                'auto_delete': True,
            }
            record._send_mail_message(template_email, template_values)

    def failed_send_mail_message(self, record_id, type:str):
        template_email = ""
        if type == "email":
            template_email = self.env.ref('send_message_cron.failed_send_mail_template')
        else:
            template_email = self.env.ref('send_message_cron.failed_send_wa_template')
        groups = self.env.ref('send_message_cron.group_failed_notif_receiver')
        record = self.env['send_message.email'].browse(int(record_id))
        for user in groups.users:
            template_values = {
                'email_from'    : self.env.company.email,
                'email_to'      : user.partner_id.email,
                'auto_delete'   : True,
            }
            record._send_mail_message(template_email, template_values)

    def failed_send_wa_message(self, type:str):
        groups = self.env.ref('send_message_cron.group_failed_notif_receiver')
        if type == "email":
            param =  self.env["ir.config_parameter"].sudo().get_param("send_message_cron.message_failed_email")
        else:
            param =  self.env["ir.config_parameter"].sudo().get_param("send_message_cron.message_failed_wa")
        for user in groups.users:
            message_wa = param.replace("{name}", user.partner_id.name)
            data = {
                'message': message_wa,
                'recipient': user.partner_id.mobile,
                'ref': "Failed Send Message"
            }
            employee = self.env['hr.employee'].search([('user_id', '=', user.id)])
            if employee and employee.mobile_phone:
                data['recipient'] = employee.mobile_phone
            self.post_wa_message(data_input=data)

                      
