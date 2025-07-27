import os
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
    _inherit = "approval.transaction.stage"
    _description = """
    
    Helper for create new Approval Hr Employee Config
    
    This model is used to configure the approval process for HR employees.
    using approval_id field to hierarchy approval process.
    """

    def button_create(self):
        pass

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
            source['approval_tasks'] = [(0, 0, 0, {"user_id": user_id, "type_approval": "user"}) for user_id in user_ids]

        # Create a new stage
        return super(ApprovalHrEmployeeConfig, self).create_new_stage(source=source)

    def reset_stage(self):
        pass


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

    def action_button_create__stage_hr_employee_id(self):
        """Action button to edit the HR employee approval configuration."""
        if not self:
            return
        self.ensure_one()
        if self.stage_hr_employee_id:
            return self.action_button_edit__stage_hr_employee_id()
        else:
            context = dict(self.env.context or {},
                           default_description=self._description,
                           default_transaction_id=self.id,
                           default_transaction_model_name=self._name,
                           default_name=self.name,
                           default_requester_id=self.delegator_id.id,
                           transaction_stage_field='stage_hr_employee_id',
                           )

            if 'transaction_stage_field' not in context:
                context['transaction_stage_field'] = 'stage_hr_employee_id'

            result = self.env['approval.strategy.hr_employee.config'].with_context(context).create_new_stage()
            if isinstance(result, dict):
                return result

            self.stage_hr_employee_id = int(result)
            return self.action_button_edit__stage_hr_employee_id()

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
