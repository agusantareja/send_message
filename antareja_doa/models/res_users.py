# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools

import logging

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    proxy_ids = fields.One2many(
        'user.delegate',
        'proxy_id',
        string='Proxy for Users',
        help="List of users delegated to this user."
    )

    proxy_user_ids = fields.Many2many(
        'res.users',
        string='Delegator Users',
        compute='_compute_proxy_user_group_ids',
        store=False,
        readonly=True,
        help="Users who delegated to this user."
    )

    proxy_group_ids = fields.Many2many(
        'res.groups',
        string='Delegator Groups',
        compute='_compute_proxy_user_group_ids',
        store=False,
        readonly=True,
        help="Groups from users who delegated to this user."
    )

    @api.depends('proxy_ids.delegator_id.groups_id')
    def _compute_proxy_user_group_ids(self):
        for user in self:
            # Ambil semua delegator dari proxy_ids
            delegators = user.proxy_ids.mapped('delegator_id')
            user.proxy_user_ids = delegators

            # Gabungkan semua group dari delegators
            group_set = self.env['res.groups'].browse()
            for delegator in delegators:
                group_set |= delegator.groups_id
            user.proxy_group_ids = group_set

    delegate_ids = fields.One2many(
        'user.delegate',
        'delegator_id',
        string='Delegated to Users',
        help="List of users delegated by this user."
    )

    def has_group(self, group_ext_id):
        # use singleton's id if called on a non-empty recordset, otherwise
        # context uid

        base_groups_access = super(ResUsers, self).has_group(group_ext_id)
        # Always return True for base.group_user
        if group_ext_id in ['base.group_user', 'base.group_system', 'base.group_erp_manager',
                            'base.user_root', 'base.user_admin']:
            return base_groups_access
        base_groups_access = self.has_delegate_group_ext_id(group_ext_id)
        if base_groups_access:
            _logger.info(
                "User %s has group %s through delegation.",
                self.login, group_ext_id
            )
        return base_groups_access
        # __ignore_delegated_user_proxy_activate veto untuk tidak melakukan pengecekan bila di lakukan di program
        # __delegated_user_group_proxy_activate dari UI
        # hack delegate user proxy activate
        # if not base_groups_access and "fleet_group_manager" in group_ext_id:
        #     print(group_ext_id)
        # if not base_groups_access and not self.env.context.get(
        #         '__ignore_delegated_user_proxy_activate') and self.env.context.get(
        #     '__delegated_user_group_proxy_activate'):
        #
        #     base_groups_access = self.has_delegate_group_ext_id(group_ext_id)
        #     if base_groups_access:
        #         _logger.info(
        #             "User %s has group %s through delegation.",
        #             self.login, group_ext_id
        #         )
        # return base_groups_access

    @api.model
    @tools.ormcache('self._uid', 'group_id')
    def has_group_id(self, group_id):
        """Checks whether user belongs to given group.
        """
        self._cr.execute("""SELECT 1 FROM res_groups_users_rel as gu
                            INNER JOIN ir_model_data d on gu.gid = d.res_id
                            WHERE uid=%s AND res_id = %s""",
                         (self._uid, group_id))
        return bool(self._cr.fetchone())

    @api.model
    def has_delegate_group_ext_id(self, group_ext_id):
        group_id = self.env.ref(group_ext_id).id
        if group_id:
            return self.has_delegate_group_id(group_id)
        else:
            return False

    def has_delegate_group_id(self, group_id: int):
        """
        Checks this user as proxy user have DoA form delegator user given group delegator user to poxy user.

        disarankan untuk menggunakan SQL agar lebih efisien
        """
        if group_id:
            uid = self.id
            if uid and uid != self._uid:
                self = self.with_user(uid)
            return self.env['user.delegate'].proxy_has_delegate_group(self._uid, group_id)
        else:
            return False

    def get_delegate_user_group(self):
        """
        Get all delegations user group for this proxy user.
        :return: {

            'user_ids': [user_id1, user_id2, ...],
            'group_ids': [group_id1, group_id2, ...]
            }
        """
        uid = self.id
        if uid and uid != self._uid:
            uid = self._uid
        return self.env['user.delegate'].get_delegations_user_group_for_proxy(uid)
