# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.addons.antareja_approval.tools.utils import to_integer
from odoo.addons.antareja_approval.tools.utils import ignore_delegated_user_context


class ApprovalAccessMixin(models.AbstractModel):
    _inherit = "approval.access.mixin"

    access_approval = fields.Boolean(
        string="Can Approve",
    )
    access_direct_approval = fields.Boolean(
        string="Can Approve by Directly User"
    )
    access_proxy_approval = fields.Boolean(
        string="Can Approve as Proxy",
    )
    access_proxy_or_direct_approval = fields.Boolean(
        string="Can Approve Directly or as Proxy",
    )


class AbstractApprovalAccess(models.AbstractModel):
    _inherit = "abstract.approval.access"

    access_approval = fields.Boolean(
        string="Can Approve Directly",
        compute="_compute_access_rights",
        search='search_filter_access_approval',
        store=False
    )

    access_direct_approval = fields.Boolean(
        string="Can Approve Directly",
        compute="_compute_access_rights",
        search='search_filter_access_approval',
        store=False
    )
    access_proxy_approval = fields.Boolean(
        string="Can Approve as Proxy",
        compute="_compute_access_rights",
        search="search_filter_access_proxy_approval",
        store=False
    )
    access_proxy_or_direct_approval = fields.Boolean(
        string="Can Approve Directly or as Proxy",
        compute="_compute_access_rights",
        search="search_filter_access_proxy_or_direct_approval",
        store=False
    )

    def search_filter_approval(self, operator, operand):
        return self.search_filter_access_proxy_or_direct_approval(operator, operand)

    def search_filter_access_direct_approval(self, operator, operand):
        # Hanya sebagai approver langsung
        user = self.env.user
        domain = ['|',
                  '&', ('type_approval', '=', 'user'), ('user_id', '=', user.id),
                  '&', ('type_approval', '=', 'group'), ('group_id', 'in', user.groups_id.ids)
                  ]
        return domain

    def search_filter_access_proxy_approval(self, operator, operand):
        # Hanya sebagai proxy
        current_user = self.env.user
        delegate = current_user.get_delegate_user_group()
        if not delegate or not delegate.get('user_delegate_ids'):
            # Jika tidak ada delegasi, kembalikan domain kosong
            return [('id', '=', False)]
        # Hanya sebagai proxy
        domain = ['|',
                  '&', ('type_approval', '=', 'user'), ('user_id', 'in', delegate.get('user_ids', [])),
                  '&', ('type_approval', '=', 'group'), ('group_id', 'in', delegate.get('group_ids', []))
                  ]
        return domain

    def search_filter_access_proxy_or_direct_approval(self, operator, operand):
        current_user = self.env.user
        delegate = current_user.get_delegate_user_group()
        if not delegate or not delegate.get('user_delegate_ids'):
            return self.search_filter_access_approval(operator, operand)
        user_ids = list(set([current_user.id] + delegate.get('user_ids', [])))  # Convert to set to remove duplicates
        group_ids = list(
            set(current_user.groups_id.ids + delegate.get('group_ids', [])))  # Combine and remove duplicates

        domain = ['|',
                  '&', ('type_approval', '=', 'user'), ('user_id', 'in', user_ids),
                  '&', ('type_approval', '=', 'group'), ('group_id', 'in', group_ids),
                  ]
        return domain

    @api.depends('type_approval', 'user_id', 'group_id')
    def _compute_access_rights(self):
        current_user = self.env.user
        delegate = current_user.get_delegate_user_group()
        delegated_user_ids = delegate.get('user_ids', [])
        delegated_group_ids = delegate.get('group_ids', [])
        user_delegations = delegate.get('user_delegate_ids', [])
        for rec in self:
            rec.access_direct_approval = False
            rec.access_proxy_approval = False

            # Approver langsung
            if rec.type_approval == 'user' and rec.user_id.id == current_user.id:
                rec.access_direct_approval = True
            elif rec.type_approval == 'group' and rec.group_id.id in current_user.groups_id.ids:
                rec.access_direct_approval = True

            if user_delegations:
                # Proxy approval
                if rec.type_approval == 'user' and rec.user_id.id in delegated_user_ids:
                    rec.access_proxy_approval = True
                elif rec.type_approval == 'group' and rec.group_id.id in delegated_group_ids:
                    rec.access_proxy_approval = True

            rec.access_proxy_or_direct_approval = rec.access_approval = rec.access_direct_approval or rec.access_proxy_approval

    def get_domain_for_current_user(self):
        proxy_only = self.env.context.get('proxy_only')
        direct_only = self.env.context.get('direct_only')
        # Delegasi aktif
        domain = []
        if (not proxy_only and not direct_only) or (proxy_only and direct_only):
            domain = self.search_filter_access_proxy_or_direct_approval('=', True)
        elif proxy_only:
            domain = self.search_filter_access_proxy_approval('=', True)
        elif direct_only:
            # Hanya sebagai approver langsung
            domain = self.search_filter_access_approval('=', True)
        else:
            # Default case, if no context is set, return all approvals
            domain = [('id', '=', False)]
        return domain

    def search_for_current_user(self):
        domain = self.get_domain_for_current_user()
        return self.search(domain)

    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        proxy_only = self.env.context.get('proxy_only')
        direct_only = self.env.context.get('direct_only')
        current_user = self.env.context.get('current_user_only') or proxy_only or direct_only
        if current_user:
            if domain:
                # If domain is provided, use it directly
                if isinstance(domain, str):
                    domain = eval(domain)
                domain.extend(self.get_domain_for_current_user())
            else:
                domain = self.get_domain_for_current_user()

        return super(AbstractApprovalAccess, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit,
                                                               order=order)
