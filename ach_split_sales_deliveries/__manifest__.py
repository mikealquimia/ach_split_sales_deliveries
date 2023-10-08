# -*- coding: utf-8 -*-
{
    'name': "Split Sales Deliveries",
    'summary': """Multi Stock Picking in Sale Order
        """,
    'description': """Obtain multiple deliveries according to sales requirements.
    """,
    'author': "ACH",
    'license': 'LGPL-3',
    'support': 'developmentalchemygx@gmail.com',
    'category': 'Sales',
    'version': '0.1',
    'live_test_url': 'https://youtu.be/EDem9LEk6z8',
    'price': 18.00,
    'depends': ['base',
                'sale_stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/update_sale_order_line.xml',
        'views/sale_order_views.xml',
    ],
    'images': ['static/description/banner.png'],
}