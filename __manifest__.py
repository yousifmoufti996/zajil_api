# -*- coding: utf-8 -*-
{
    'name': 'Alzajel Shipping Integration',

    'summary': 'Integration with Alzajel Shipping Services',
    'description': """
        Integrate Odoo with Alzajel Shipping Service
                - Track shipment status
                - Store tracking information
                - Automatic status updates
            """,
    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Inventory/Delivery',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['stock', 'delivery'],
    'data': [
        # 'security/ir.model.access.csv',
        # 'wizard/alzajel_shipping_wizard_views.xml',
        # 'views/res_config_settings_views.xml',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}

