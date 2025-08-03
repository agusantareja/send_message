# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools
from datetime import date
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class UserDelegate(models.Model):
    _name = 'user.delegate'
    _description = 'User Delegation'
    _order = 'start_date desc'
    _inherit = ['mail.thread']

    active = fields.Boolean(default=True)
    name = fields.Char(string='Delegation Number', default='Draft', required=True, tracking=True, copy=False)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, string='Company', tracking=True,
        help="Company for which the delegation is valid."
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('prepared', 'prepared'),
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ], string='State', default='draft', tracking=True)
    delegator_id = fields.Many2one(
        'res.users', string='Delegator', required=True, tracking=True, default=lambda self: self.env.user)
    delegator_group_ids = fields.Many2many(
        'res.groups',
        string='Delegator Groups',
        compute='_compute_delegator_group_ids',
        store=False,  # jika ingin nilainya disimpan di DB
        readonly=True,  # agar tidak bisa diubah manual
        help="Groups of the delegator user. Used for filtering delegations."
    )

    @api.depends('delegator_id')
    def _compute_delegator_group_ids(self):
        for rec in self:
            if rec.delegator_id:
                rec.delegator_group_ids = rec.delegator_id.groups_id
            else:
                rec.delegator_group_ids = [(5, 0, 0)]

    proxy_id = fields.Many2one('res.users', string='Proxy (Acting On Behalf)', required=True, tracking=True)
    start_date = fields.Date(string='Start Date', required=True, tracking=True)
    end_date = fields.Date(string='End Date', required=True, tracking=True)
    note = fields.Text(string="Notes")

    def name_get(self):
        return [(record.id, f"[{record.name}] {record.delegator_id.name} to {record.proxy_id.name}") for record in self]

    def ensure_set_number(self):
        name = self.name or 'Draft'
        if name in ['Draft', 'New'] and self.state != 'draft':
            find_dcr = True
            # Jika sudah ada, buat nomor baru sampai tidak ada yang sama
            while find_dcr:
                name = self.env['ir.sequence'].next_by_code('user.delegate') or 'Draft'
            self.write({'name': name})

    def _set_prepared_state(self):
        self.ensure_one()
        self.ensure_set_number()
        today = date.today()
        if self.start_date > today:
            self.state = 'prepared'
        if self.end_date < today:
            self.state = 'expired'
        else:
            self.state = 'active'

    def action_button_submit(self):
        self._set_prepared_state()

    def get_prepared_state(self):
        return ['prepared']

    def cron_update_delegation_state(self):
        """
        Cron job to update the state of delegations based on current date.
        """
        today = date.today()
        delegations = self.search([('state', 'in', self.get_prepared_state())])
        for delegation in delegations:
            if delegation.state == 'prepared':
                continue

            if delegation.start_date > today:
                delegation.state = 'prepared'
            elif delegation.end_date < today:
                delegation.state = 'expired'
            else:
                delegation.state = 'active'

            delegation.ensure_set_number()

    @api.constrains('delegator_id', 'proxy_id')
    def _check_different_users(self):
        for rec in self:
            if rec.delegator_id == rec.proxy_id:
                raise ValidationError("Delegator and Proxy cannot be the same user.")

    @api.model
    def get_proxy_for_user(self, user_id, company_id=None):
        today = date.today()
        domain = [
            ('delegator_id', '=', user_id),
            ('start_date', '<=', today),
            ('end_date', '>=', today),
            ('state', '=', 'active')
        ]
        if company_id:
            domain.extend([
                ('delegator_id.company_ids', '=', company_id),
                ('proxy_id.company_ids', '=', company_id)
            ]
            )
        delegation = self.search(domain, )
        return delegation.proxy_id if delegation else False

    def get_all_delegations_for_proxy(self, proxy_id=None, user_id=None, group_id=None, company_id=None, user_ids=None,
                                      limit=None):
        """
        Ambil delegasi aktif untuk proxy tertentu.
        Jika group_id diberikan, hanya delegator yang termasuk dalam grup tersebut.
        """
        today = date.today()
        domain = [
            ('start_date', '<=', today),
            ('end_date', '>=', today),
            ('state', '=', 'active')
        ]
        if company_id:
            domain.extend([
                ('delegator_id.company_ids', '=', company_id),
                ('proxy_id.company_ids', '=', company_id)
            ])

        if proxy_id:
            domain.append(('proxy_id', '=', proxy_id))

        if user_id and group_id:
            raise ValidationError("You cannot filter by both user_id and group_id at the same time.")

        if user_ids:
            domain.append(('delegator_id', 'in', user_ids))
        elif user_id:
            domain.append(('delegator_id', '=', user_id))

        if group_id:
            # group = self.env['res.groups'].browse(group_id)
            domain.append(('delegator_id.groups_id', '=', group_id))

        return self.search(domain, limit=limit)

    def get_delegations_for_proxy(self, proxy_id, **kwargs):
        return self.get_all_delegations_for_proxy(proxy_id, limit=1, **kwargs)

    @tools.ormcache('proxy_id')
    def get_delegations_user_group_for_proxy(self, proxy_id):
        # _logger.debug("Getting delegation info from DB for proxy_id=%s", proxy_id)
        # today = date.today()
        # domain = [
        #     ('start_date', '<=', today),
        #     ('end_date', '>=', today),
        #     ('state', '=', 'active'),
        #     ('proxy_id', '=', proxy_id)
        # ]
        # user_delegations = self.sudo.search(domain)
        # delegated_user_ids = list(set(user_delegations.mapped('delegator_id.id')))
        # delegated_group_ids = list(set(user_delegations.mapped('delegator_id.groups_id.id')))
        # return {
        #     'user_ids': delegated_user_ids,
        #     'group_ids': delegated_group_ids,
        # }
        #
        _logger.debug("Getting delegation info from DB for proxy_id=%s (SQL)", proxy_id)
        self._cr.execute("""
                SELECT DISTINCT ud.id, ud.delegator_id, gu.gid
                FROM user_delegate ud
                JOIN res_groups_users_rel gu ON gu.uid = ud.delegator_id
                WHERE
                    ud.proxy_id = %s
                    AND ud.state = 'active'
                    AND ud.start_date <= CURRENT_DATE
                    AND ud.end_date >= CURRENT_DATE
            """, (proxy_id,))
        rows = self._cr.fetchall()

        # Pisahkan jadi dua set
        user_ids = set()
        group_ids = set()
        user_delegate_ids = set()
        for udid , uid, gid in rows:
            user_ids.add(uid)
            group_ids.add(gid)
            user_delegate_ids.add(udid)

        return {
            'user_ids': list(user_ids),
            'group_ids': list(group_ids),
            'user_delegate_ids': list(user_delegate_ids),
        }

    @tools.ormcache('proxy_id', 'group_id', 'company_id')
    def proxy_has_delegate_group_company(self, proxy_id, group_id, company_id):
        """
        Checks this user as proxy user have DoA form delegator user given group delegator user to proxy user.
        """
        # today = date.today()
        # domain = [
        #     ('start_date', '<=', today),
        #     ('end_date', '>=', today),
        #     ('state', '=', 'active'),
        #     ('proxy_id', '=', proxy_id),
        #     ('proxy_id.company_ids', '=', company_id),
        #     ('delegator_id.company_ids', '=', company_id),
        #     ('delegator_id.groups_id', '=', group_id)
        # ]
        # base_groups_access = self.sudo().search(domain, limit=1)
        # return base_groups_access and True or False
        self._cr.execute("""
                SELECT 1
                FROM user_delegate ud
                JOIN res_groups_users_rel gu ON gu.uid = ud.delegator_id
                WHERE
                    ud.proxy_id = %s
                    AND gu.gid = %s
                    AND ud.state = 'active'
                    AND ud.start_date <= CURRENT_DATE
                    AND ud.end_date >= CURRENT_DATE
                    AND ud.company_id = %s
                LIMIT 1
            """, (proxy_id, group_id, company_id))
        return bool(self._cr.fetchone())

    @tools.ormcache('proxy_id', 'group_id')
    def proxy_has_delegate_group(self, proxy_id, group_id):
        """
        Checks this user as proxy user have DoA form delegator user given group delegator user to proxy user.
        """
        # today = date.today()
        # domain = [
        #     ('start_date', '<=', today),
        #     ('end_date', '>=', today),
        #     ('state', '=', 'active'),
        #     ('proxy_id', '=', proxy_id),
        #     ('delegator_id.groups_id', '=', group_id)
        # ]
        # base_groups_access = self.sudo().search(domain, limit=1)
        # return base_groups_access and True or False
        self._cr.execute("""
            SELECT 1
            FROM user_delegate ud
            JOIN res_groups_users_rel gu ON gu.uid = ud.delegator_id
            WHERE
                ud.proxy_id = %s
                AND gu.gid = %s
                AND ud.state = 'active'
                AND ud.start_date <= CURRENT_DATE
                AND ud.end_date >= CURRENT_DATE
            LIMIT 1
        """, (proxy_id, group_id))
        return bool(self._cr.fetchone())

    def _clear_proxy_cache_if_needed(self, old_vals=None):
        """
        Bersihkan cache hanya jika:
        - state berubah menjadi atau dari 'active'
        - atau field penting pada delegasi aktif berubah
        """
        tracked_fields = {'start_date', 'end_date', 'delegator_id', 'proxy_id', 'state'}

        for rec in self:
            need_clear = False

            # Jika tidak disediakan, bersihkan saja tanpa pengecekan
            if old_vals is None:
                need_clear = True
            else:
                # Cek perubahan state
                old_state = old_vals.get(rec.id, {}).get('state')
                new_state = rec.state
                if old_state != new_state and ('active' in (old_state, new_state)):
                    need_clear = True

                # Jika state tetap 'active', cek field lain berubah
                if old_state == 'active' and new_state == 'active':
                    for field in tracked_fields:
                        if field in old_vals.get(rec.id, {}):
                            need_clear = True
                            break

            if need_clear and rec.proxy_id:
                _logger.debug("Clearing cache for proxy_id=%s due to state/field change.", rec.proxy_id.id)
                self.get_delegations_user_group_for_proxy.clear_cache(self, rec.proxy_id.id)

                if rec.delegator_id:
                    for group in rec.delegator_id.groups_id:
                        self.proxy_has_delegate_group.clear_cache(self, rec.proxy_id.id, group.id)

                        for company in rec.delegator_id.company_ids:
                            _logger.debug(
                                "Clearing cache for proxy_id=%s, group_id=%s, company_id=%s",
                                rec.proxy_id.id, group.id, company.id
                            )
                            self.proxy_has_delegate_group_company.clear_cache(
                                self, rec.proxy_id.id, group.id, company.id
                            )

    def setup_number(self, vals):
        if vals.get('name', 'Draft') in ['Draft', 'New']:
            find_dcr = True
            while find_dcr:
                vals['name'] = self.env['ir.sequence'].next_by_code('user.delegate') or 'New'
                find_dcr = self.search([('name', '=', vals['name'])], limit=1)
        return vals

    def write(self, vals):
        old_vals = {}
        if any(field in vals for field in ['state']):
            for rec in self:
                old_vals[rec.id] = {
                    field: rec[field] for field in vals.keys() if field in rec
                }

        result = super().write(vals)
        if self.name in ['Draft', 'New']:
            if not self.env.context.get('__setup_number'):
                self = self.with_context(__setup_number=True)
                new_vals = self.setup_number({'name': self.name})
                self.write(new_vals)
                self.flush()
            else:
                return result
        # self._clear_proxy_cache_if_needed(old_vals)
        return result

    @api.model_create_multi
    def create(self, vals_list):
        new_vals_list = []
        for vals in vals_list:
            new_vals_list.append(self.setup_number(vals))

        records = super().create(new_vals_list)

        # Hapus cache hanya untuk yang state-nya langsung 'active'
        # active_records = records.filtered(lambda r: r.state == 'active')
        # active_records._clear_proxy_cache_if_needed()
        return records

    def unlink(self):
        active_records = self.filtered(lambda r: r.state == 'active')
        proxies = active_records.mapped('proxy_id')
        res = super().unlink()
        for proxy in proxies:
            self.get_delegations_user_group_for_proxy.clear_cache(self, proxy.id)
        return res

    @api.constrains('delegator_id', 'proxy_id', 'start_date', 'end_date', 'state')
    def _check_duplicate_active_delegation(self):
        for rec in self:
            if rec.state == 'cancelled':
                continue
            overlaps = self.search([
                ('id', '!=', rec.id),
                ('state', '=', 'active'),
                ('delegator_id', '=', rec.delegator_id.id),
                ('proxy_id', '=', rec.proxy_id.id),
                ('start_date', '<=', rec.end_date),
                ('end_date', '>=', rec.start_date),
            ])
            if overlaps:
                raise ValidationError("Duplicate active delegation with overlapping period found.")
