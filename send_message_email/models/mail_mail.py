# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class MailMail(models.Model):
    _inherit = 'mail.mail'

    def get_send_message_email_test(self):
        return self.env['ir.config_parameter'].get_param('send_message_cron.test_email')

    @api.model
    def create(self, values):
        # intercepting for test environment
        test_email = self.get_send_message_email_test()
        if test_email and test_email != 'False':
            _logger.info(f"TO: {values.get('email_to')} CC: {values.get('email_cc')} RR: {values.get('recipient_ids')} --> {test_email}")
            values['email_to'] = test_email
            if 'email_cc' in values:
                values.pop('email_cc')
            if 'recipient_ids' in values:
                values.pop('recipient_ids')

        return super(MailMail, self).create(values)
