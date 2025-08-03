# -*- coding: utf-8 -*-
{
    'name': "Approval",

    'summary': """
        Add Feature DOA to Approval Task 
        """,

    'description': """
        This module adds a feature for Delegation of Authority (DOA) Approval.
        It allows users to delegate authority and manage approval transactions
        with a focus on human resources and employee strategies.
    """,

    'author': "Agus Muhammad Ramdan",
    'website': "http://www.yourcompany.com",

    'category': 'Approval & Delegation of Authority',
    'version': '13.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'antareja_approval', 'antareja_doa'],

    # always loaded
    'data': [
        'views/approval_transaction_task_views.xml',
        'views/approval_audit_log_views.xml',
    ],
}
