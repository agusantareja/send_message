# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.antareja_approval.models.abstract_approval_stage import APPROVAL_STATUS_NOT_APPROVE, \
    APPROVAL_STATUS_APPROVED, APPROVAL_STATUS_REJECTED, \
    APPROVAL_STATUS_CANCELLED, APPROVAL_STATUS_LIST


def have_method(obj, method):
    return hasattr(obj, method) and callable(getattr(obj, method))


def to_integer(value):
    """
    Convert a value to an integer if it is not None.
    If the value is None, return None.
    """
    if value is None:
        return None
    if value is False:
        return False

    if value:
        try:
            return int(value)
        except (ValueError, TypeError):
            if isinstance(value, models.BaseModel):  # jika recordset
                return value.id

    return value


class AbstractApprovalTransaction(models.AbstractModel):
    _inherit = 'abstract.approval.task'

    user_delegate_id = fields.Many2one(
        'user.delegate'
    )
    user_behalf_of_id = fields.Many2one(
        'res.users',
        'User Behalf Of',
        help="User on behalf of whom the transaction is executed"
    )

    def check_delegated_user(self):
        self.ensure_one()
        if not self.access_approval:
            if self.access_proxy_approval:
                delegate = self.get_user_delegate()

                if not delegate:
                    raise ValidationError("Delegator not found.")
                delegate = to_integer(delegate)
                self.user_delegate_id = delegate
                context = dict(self.env.context, __user_delegate_id=delegate)
                self = self.with_user(delegate.delegator_id).with_context(context)
            else:
                raise ValidationError("You are not authorized to approve this transaction.")
        else:
            self.user_delegate_id = None
        return self

    def _approve_task(self, **kwargs):
        """Approve the transaction"""
        self = self.check_delegated_user()
        self.ensure_one()
        self.validate_before_approve_or_reject()
        user_delegate_id = self.env.context.get('__user_delegate_id')
        self.user_delegate_id = user_delegate_id
        # Tandai status
        self.status_approval = APPROVAL_STATUS_APPROVED
        self.date_execution = fields.Datetime.now()
        if user_delegate_id:
            delegator = self.user_delegate_id.delegator_id
            proxy_user = self.user_delegate_id.proxy_id
            self.user_execution_id = proxy_user.id
            self.user_behalf_of_id = delegator.id
            self.create_audit_trial(
                'proxy_approve',
                notes='Approve via proxy',
                proxy_user_id=proxy_user.id,
            )
        else:
            self.user_delegate_id = False
            self.user_execution_id = self.env.user.id
            self.create_audit_trial('approve', notes='Approve')

        approval_stage_object = kwargs.get('approval_stage_object') or self.get_approval_stage_object()
        kwargs['approval_stage_object'] = approval_stage_object
        approval_stage_object.callback_approval_task_approved(self, **kwargs)

    def get_user_delegate(self, raise_exception=True):
        self.ensure_one()
        if self.type_approval == 'user':
            # Delegasi tipe user
            return self.env['user.delegate'].sudo().get_delegations_for_proxy(
                proxy_id=self.env.user.id,
                user_id=self.user_id.id,
            )

        elif self.type_approval == 'group':
            # Delegasi tipe group
            return self.env['user.delegate'].sudo().get_delegations_for_proxy(
                proxy_id=self.env.user.id,
                group_id=self.group_id.id,
            )
        elif raise_exception:
            raise ValidationError("Invalid approval type. Must be 'user' or 'group'.")
        else:
            return self.env['user.delegate'].browse([])

    def _reject_task(self, **kwargs):
        self = self.check_delegated_user()
        """Reject the transaction"""
        self.validate_before_approve_or_reject()
        self.status_approval = APPROVAL_STATUS_REJECTED
        self.date_execution = fields.Datetime.now()
        reject_reason = self.env.context.get('__reject_reason')
        self.reason_approval = reject_reason
        user_delegate_id = self.env.context.get('__user_delegate_id')
        self.user_delegate_id = user_delegate_id
        if user_delegate_id:
            delegator = self.user_delegate_id.delegator_id
            proxy_user = self.user_delegate_id.proxy_id
            self.user_execution_id = proxy_user.id
            self.user_behalf_of_id = delegator.id
            self.create_audit_trial('proxy_reject')
        else:
            self.user_delegate_id = False
            self.user_execution_id = self.env.user.id
            self.create_audit_trial('reject')

        approval_stage_object = kwargs.get('approval_stage_object') or self.get_approval_stage_object()
        kwargs['approval_stage_object'] = approval_stage_object
        approval_stage_object.callback_approval_task_rejected(self, **kwargs)

    def prepare_dict_audit_trial(self):
        prepare_dict = super(AbstractApprovalTransaction, self).prepare_dict_audit_trial()
        prepare_dict.update({
            'user_delegate_id': self.user_delegate_id.id,
        })
        return prepare_dict

    def create_audit_trial(self, action_type, ignore_message=False, **kwargs):
        prepare_dict = self.prepare_dict_audit_trial()
        prepare_dict.update(kwargs)

        if self.user_delegate_id:
            proxy_user_id = to_integer(self.user_delegate_id.proxy_id)
            user_delegate_id = to_integer(self.user_delegate_id)
            prepare_dict.update(
                user_delegate_id=user_delegate_id,
                user_id=proxy_user_id,
                proxy_user_id=proxy_user_id,
            )
            if action_type == 'approve':
                action_type = 'proxy_approve'
            elif action_type == 'reject':
                action_type = 'proxy_reject'

        prepare_dict['action_type'] = action_type
        self.approval_audit_log_id = self.approval_audit_log_id.create_audit_log(
            without_send_message=ignore_message,
            **prepare_dict
        )

        return self.approval_audit_log_id
