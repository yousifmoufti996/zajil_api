from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    alzajel_auth_key = fields.Char(
        string='Alzajel Auth Key',
        config_parameter='alzajel.auth_key'
    )
    alzajel_vendor_id = fields.Char(
        string='Alzajel Vendor ID',
        config_parameter='alzajel.vendor_id'
    )
    alzajel_api_url = fields.Char(
        string='Alzajel API URL',
        config_parameter='alzajel.api_url',
        default='https://alzajelservice.com/api'
    )