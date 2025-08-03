from odoo import models, fields, api


def have_method(obj, method):
    return hasattr(obj, method) and callable(getattr(obj, method))


class AbstractApprovalAuditLog(models.AbstractModel):
    _inherit = 'abstract.approval.audit.log'
    _description = 'Approval Audit Log'
    _order = 'create_date desc'

    proxy_user_id = fields.Many2one('res.users', string="Acting User")
    delegator_user_id = fields.Many2one('res.users', string="On Behalf Of")
    user_delegate_id = fields.Many2one('user.delegate', string="Delegate Rule")


class ApprovalAuditLog(models.Model):
    _inherit = 'approval.audit.log'

    def send_message(self):
        rec = self.ensure_one()
        Notification = self.env["abstract.approval.notification"]
        parent_document = self.get_transaction_object()
        if rec.action_type in ['proxy_reject', 'reject']:
            message = Notification.get_reject_transaction_comment_message(
                rec_object=parent_document,
                action_type=rec.action_type)
            Notification.reject_transaction_comment(
                rec_object=parent_document,
                message=message,
                action_type=rec.action_type)
        elif rec.action_type in ['proxy_approve', 'approve']:
            message = Notification.get_approved_transaction_comment_message(
                rec_object=parent_document,
                action_type=rec.action_type)
        else:
            return

        if parent_document and have_method(parent_document, 'message_post'):
            parent_document.message_post(body=message)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'user_delegate_id' in vals:
                user_delegate = self.user_delegate_id.browse(vals['user_delegate_id'])
                if not vals.get('proxy_user_id'):
                    vals['proxy_user_id'] = user_delegate.proxy_id.id
                if not vals.get('delegator_user_id'):
                    vals['delegator_user_id'] = user_delegate.delegator_id.id

        return super(ApprovalAuditLog, self).create(vals_list)
