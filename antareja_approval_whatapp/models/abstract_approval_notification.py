# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

_logger = __import__('logging').getLogger(__name__)


def have_method(obj, method):
    return hasattr(obj, method) and callable(getattr(obj, method))


class AbstractApprovalNotification(models.AbstractModel):
    _inherit = "abstract.approval.notification"

    def mail_bot_approve_user(self, user, message, **kwargs):
        super(AbstractApprovalNotification, self).mail_bot_approve_user(user, message, **kwargs)
        transaction_object = (kwargs.get('transaction_object') or self.get_transaction_object(**kwargs))
        if transaction_object and 'transaction_object' not in kwargs:
            kwargs['transaction_object'] = transaction_object
        self.env["send_message.whatsapp"].send_message_whatsapp(message, user.mobile_phone, ref=transaction_object.name)
