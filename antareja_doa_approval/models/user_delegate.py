# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date
from odoo.exceptions import ValidationError
from odoo.addons.antareja_approval.tools.exception import ShowWizardFormError


class UserDelegate(models.Model):
    _name = 'user.delegate'
    _inherit = [
        _name,
        'approval.strategy.hr_employee.mixin',
        'abstract.approval.notification',
        'approval.strategy.mixin',
    ]

    # active = fields.Boolean(default=True)
    # name = fields.Char(string='Delegation Number', default='Draft', required=True, tracking=True, copy=False)
    state = fields.Selection(selection_add=[
        ('draft',),
        ('waiting_approval', 'Waiting Approval'),
        ('approved', 'Approved'),
    ])

    def get_requester_id(self):
        """ Return the ID of the delegator user. """
        self.ensure_one()
        return self.delegator_id.id

    def action_button_submit(self):
        self.ensure_one()
        try:
            return self.strategy_button_submit()
        except ShowWizardFormError as e:
            return e.get_action_form()
