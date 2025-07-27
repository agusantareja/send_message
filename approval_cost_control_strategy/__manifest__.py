# -*- coding: utf-8 -*-
{
    'name': "DOA Approval",

    'summary': """
        Add Feature DOA Approval for Antareja Intranet""",

    'description': """
        This module adds a feature to Antareja Intranet for managing Delegation of Authority (DOA) approvals.
        It allows users to delegate their approval tasks to other users, enhancing workflow efficiency and flexibility.
        The module includes functionalities for defining user delegates, managing approval tasks, and tracking approval statuses.
        Key Features:
        - Define user delegates for approval tasks
        - Manage approval tasks and their statuses
        - Track approval history and actions
        - Integration with existing Antareja Intranet modules
    """,

    'author': "Agus Muhammad Ramdan",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'hr', 'antareja_approval'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/user_delegate_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
