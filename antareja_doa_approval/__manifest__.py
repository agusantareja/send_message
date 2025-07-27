# -*- coding: utf-8 -*-
{
    'name': "DOA Approval",

    'summary': """
        Add Feature DOA Approval 
        for Delegation of Authority in Approval Transactions
        with a focus on Human Resources and Employee Strategies
        """,

    'description': """
        This module adds a feature for Delegation of Authority (DOA) Approval.
        It allows users to delegate authority and manage approval transactions
        with a focus on human resources and employee strategies.
    """,

    'author': "Agus Muhammad Ramdan",
    'website': "http://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'hr', 'antareja_approval', 'approval_employee_strategy'],

    # always loaded
    'data': [
        'views/user_delegate_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
