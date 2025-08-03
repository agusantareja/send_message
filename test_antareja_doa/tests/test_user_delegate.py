from odoo.tests.common import TransactionCase, tagged
from datetime import date, timedelta


@tagged('-standard', 'test_user_delegate')
class TestUserDelegate(TransactionCase):

    def setUp(self):
        super().setUp()
        Users = self.env['res.users'].with_context(no_reset_password=True)

        self.user_1 = Users.create({
            'name': 'Delegator',
            'login': 'delegator@example.com',
            'email': 'delegator@example.com',
        })

        self.user_2 = Users.create({
            'name': 'Proxy',
            'login': 'proxy@example.com',
            'email': 'proxy@example.com',
        })

        today = date.today()
        self.delegation = self.env['user.delegate'].sudo().create({
            'name': 'Test',
            'delegator_id': self.user_1.id,
            'proxy_id': self.user_2.id,
            'start_date': today - timedelta(days=1),
            'end_date': today + timedelta(days=1),
            'state': 'active',
        })

    def test_cache_populated(self):
        proxy = self.user_2.with_context(__delegated_user_group_proxy_activate=True)
        result = self.env['user.delegate'].get_delegations_user_group_for_proxy(proxy.id)
        self.assertIn(self.user_1.id, result['user_ids'])

    def test_cache_cleared_on_unlink(self):
        proxy = self.user_2.with_context(__delegated_user_group_proxy_activate=True)
        self.delegation.unlink()
        result = self.env['user.delegate'].get_delegations_user_group_for_proxy(proxy.id)
        self.assertNotIn(self.user_1.id, result['user_ids'])

    def test_cache_cleared_on_update(self):
        proxy = self.user_2.with_context(__delegated_user_group_proxy_activate=True)
        self.delegation.write({'state': 'cancelled'})
        result = self.env['user.delegate'].get_delegations_user_group_for_proxy(proxy.id)
        self.assertNotIn(self.user_1.id, result['user_ids'])
