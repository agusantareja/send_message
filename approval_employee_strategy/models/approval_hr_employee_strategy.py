import os

from odoo.addons.antareja_approval.tools.exception import ShowWizardFormError
from odoo import models, fields, api
import requests
import logging

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    approver_id = fields.Many2one(
        'hr.employee',
        string='Approver'
    )


class ApprovalHrEmployeeConfig(models.TransientModel):
    _name = "approval.strategy.hr_employee.config"
    _inherit = ["approval.strategy.config"]
    _table = "approval_strategy_config"
    _description = """
    
    Helper for create new Approval Hr Employee Config
    
    This model is used to configure the approval process for HR employees.
    using approval_id field to hierarchy approval process.
    """

    def create_new_stage(self, source=None):
        """Create a new approval stage for HR employee."""
        source['transaction_stage_field'] = self.env.context.get('transaction_stage_field', 'stage_hr_employee_id')
        user_ids = []
        employees = self.env["hr.employee"].search([('user_id', '=', self.env.context.get('default_requester_id'))])
        if len(employees) == 1:
            emp = employees[0]
            while emp.approver_id and user_ids < 2:
                emp = emp.approver_id
                if emp.user_id:
                    user_ids.append(emp.user_id.id)

        if user_ids:
            source['approval_tasks'] = \
                [(0, 0, 0,
                  {
                      "user_id": user_id,
                      "type_approval": "user"
                  }) for user_id in user_ids]
        else:
            raise self.raise_error(source, message="No approver found for the HR employee.", )

        # Create a new stage
        return super(ApprovalHrEmployeeConfig, self).create_new_stage(source)


class ApprovalHrEmployeeMixin(models.AbstractModel):
    _name = "approval.strategy.hr_employee.mixin"
    _description = """
        Mixin for Approval HR Employee Strategy
        This mixin provides methods to handle approval stages for HR employees.
        It allows the creation and editing of approval stages specifically for HR employee transactions.
        It is used in conjunction with the `approval.transaction.stage` model to manage the approval process.
        It is designed to be inherited by models that require HR employee approval stages.
        It provides methods to create and edit the approval stage configuration for HR employees.
        It is expected that the inheriting model will have a field `stage_hr_employee_id` of type `Many2one`
        that links to the `approval.transaction.stage` model.
        It provides an action button to create or edit the HR employee approval configuration.
    """

    stage_hr_employee_id = fields.Many2one(
        'approval.transaction.stage',
        string='Stage',
        help="Stage HR Employee configuration for approval process"
    )

    def get_approval_strategy_config(self):
        return {
            'stage_hr_employee_id': ['approval.strategy.hr_employee.mixin', True]
        }

    def setup_approval_by_strategy(self):
        self._create__stage_hr_employee_id()

    def setup_approval_stage(self):
        self.ensure_one()

        self.approval_tasks.setup_approval_task()

    def _update_stage(self,
                      config_model='approval.strategy.hr_employee.config',
                      transaction_stage_field='stage_hr_employee_id'):
        """Update the stage HR employee configuration."""
        self.ensure_one()
        data = self[transaction_stage_field]
        approval_stage_id = data.id
        approval_stage_model_name = data._name
        strategy_config = self.env[config_model]
        return strategy_config.edit_form(
            transaction_stage_field=transaction_stage_field,
            transaction_id=self.id,
            transaction_model_name=self._name,
            approval_stage_id=approval_stage_id,
            approval_stage_model_name=approval_stage_model_name,
        )

    def _create__stage_hr_employee_id(self, force_create=False):
        if self.stage_hr_employee_id and not force_create:
            return

        source = {
            'description': self._description,
            'transaction_id': self.id,
            'transaction_model_name': self._name,
            'name': self.name,
            'requester_id': self.delegator_id.id,
            'transaction_stage_field': 'stage_hr_employee_id',
        }
        context = dict(self.env.context or {})
        try:
            self.stage_hr_employee_id = self.env['approval.strategy.hr_employee.config'].with_context(
                context).create_new_stage(source)
        except ShowWizardFormError as e:
            raise e

    def action_button_create__stage_hr_employee_id(self):
        """Action button to edit the HR employee approval configuration."""
        if not self:
            return
        self.ensure_one()
        try:
            self._create__stage_hr_employee_id()
        except ShowWizardFormError as e:
            return e.get_action_form()

        if self.stage_hr_employee_id:
            return self._update_stage(
                config_model='approval.strategy.hr_employee.config',
                transaction_stage_field='stage_hr_employee_id'
            )

    def action_button_edit__stage_hr_employee_id(self):
        """Action button to edit the HR employee approval configuration."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.stage_hr_employee_id._name,
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.stage_hr_employee_id.id,
            'context': dict(
                self.env.context,
                create=False
            )
        }
