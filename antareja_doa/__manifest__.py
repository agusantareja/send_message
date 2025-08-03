# -*- coding: utf-8 -*-
{
    'name': "Delegation of Authority (DoA)",

    'summary': """
        Delegation of Authority (DoA)
        """,

    'description': """
        This module adds a feature for Delegation of Authority (DOA).
        It allows users to delegate authority form access.
    """,

    'author': "Agus Muhammad Ramdan",
    'website': "http://www.yourcompany.com",

    'category': 'Security & Access Rights',
    'version': '13.0.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail'],

    # always loaded
    'data': [
        'data/user_delegate_cron.xml',
        'data/user_delegate_sequence.xml',
        'security/ir.model.access.csv',
        'views/user_delegate_views.xml',
        'views/menuitem_views.xml',
    ],
}
