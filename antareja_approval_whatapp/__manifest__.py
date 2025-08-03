# -*- coding: utf-8 -*-
{
    'name': "Approval integeration Whatapp",

    'summary': """
        Add Feature Integaration with whatapp
        """,

    'description': """
        Integeration send chanel to whataspps
    """,

    'author': "Agus Muhammad Ramdan",
    'website': "http://www.yourcompany.com",

    'category': 'Approval & Delegation of Authority',
    'version': '13.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'antareja_approval', 'send_message_whatsapp'],

    # always loaded
    'data': [
        'views/approval_transaction_task_views.xml',
        'views/approval_audit_log_views.xml',
    ],
}
