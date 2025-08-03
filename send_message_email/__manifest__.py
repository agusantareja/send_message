# -*- coding: utf-8 -*-
{
    'name': "Send Message Email",

    'summary': """Email Batch size configuration and intercept email to test adderss""",

    'description': """
        
    """,

    'author': "Agus Muhammad Ramdan",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '13.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail'],

    # always loaded
    'data': [
        'views/res_config_settings_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
