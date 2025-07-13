# -*- coding: utf-8 -*-
{
    'name': "Send Message Queue",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Fix email and whatsapp message queue
    """,

    'author': "Agus Muhammad Ramdan",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'queue_job', 'send_message_cron'],

    # always loaded
    'data': [
        # 'data/template_email_failed.xml',
        # 'data/template_wa_failed.xml',
        # 'security/res_groups.xml',
        # 'security/ir.model.access.csv',
        # 'data/send_email_cron.xml',
        # 'data/parameter.xml',
        # 'views/log.xml',
        # 'views/email.xml',
        # 'views/views.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}