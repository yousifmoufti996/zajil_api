from odoo import models, fields, api

class AlzajelShippingUpdateWizard(models.TransientModel):
    _name = 'alzajel.shipping.update.wizard'
    _description = 'Update Alzajel Shipping Details'

    picking_id = fields.Many2one('stock.picking', string='Delivery Order', required=True)
    shipment_type = fields.Selection([
        ('1', 'Cargo'),
        ('2', 'Document'),
        ('3', 'Special Category/Home Appliances')
    ], string='Shipment Type', required=True)
    delivery_type = fields.Selection([
        ('1', 'Ordinary'),
        ('2', 'Express')
    ], string='Delivery Type', required=True)
    delivery_fee_by = fields.Selection([
        ('1', 'Customer'),
        ('2', 'Merchant')
    ], string='Delivery Fee Paid By', required=True)
    order_notes = fields.Text('Delivery Notes')

    def action_update_shipping(self):
        """Update the delivery order and Alzajel shipping"""
        self.ensure_one()
        
        # Update picking with new values
        self.picking_id.write({
            'alzajel_shipment_type': self.shipment_type,
            'alzajel_delivery_type': self.delivery_type,
            'alzajel_delivery_fee_by': self.delivery_fee_by,
            'alzajel_order_notes': self.order_notes,
        })
        
        # Call the update API
        return self.picking_id.action_update_alzajel_order()