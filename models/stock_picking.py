import requests
import json
import logging
from odoo import models, fields, exceptions , _, api
from datetime import datetime

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    zajil_delivery_code = fields.Char(string='Zajil Delivery Code', readonly=True)
    zajil_tracking_url = fields.Char(string='Zajil Tracking URL', readonly=True)
    zajil_receipt_url = fields.Char(string='Zajil Receipt URL', readonly=True)

    def process_sajil_delivery(self):
        # Prepare Zajil shipment data
        zajil_data = self._prepare_zajil_data()

        # Send request to Zajil API
        response = self._send_zajil_request(zajil_data)

        if response.get('success'):
            # Update picking with Zajil tracking information
            self.write({
                'carrier_tracking_ref': response.get('order_id'),
                'zajil_delivery_code': response.get('delivery_code'),
                'zajil_tracking_url': response.get('track_url'),
                'zajil_receipt_url': response.get('orderReciptUrl')
            })

            # Call parent validation
            res = super(StockPicking, self).button_validate()

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _("The shipment has been successfully sent to Zajil."),
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            raise exceptions.UserError(_("Failed to create Zajil shipment"))

    def _prepare_zajil_data(self):
        # Get related sale order or invoice
        invoice = self.env['account.move'].sudo().search([
            ('invoice_origin', '=', self.origin)
        ], limit=1)

        if not invoice:
            raise exceptions.UserError('No invoice found')

        # Prepare package details
        package_details = []
        for move_line in self.move_line_ids:
            package_details.append({
                "length": "30",  # You may want to get these from product packaging
                "width": "30",
                "height": "30",
                "package_weight": str(move_line.product_id.weight),
                "package_price": move_line.sale_price  # Assuming you have sale price
            })

        # Prepare API payload
        zajil_data = {
            "vendor_id": "YOUR_VENDOR_ID",  # Configure in system parameters
            "order_notes": invoice.narration or "",
            "shipment_type_id": "2",  # Document
            "Delivery_Fee_pay_By": 1,  # Customer pays
            "delivery_type": "1",  # Ordinary
            "pick_up_details": {
                "pick_up_customer_name": self.company_id.name,
                "pick_up_customer_phone": self.company_id.phone,
                "pick_up_location": [0, 0],  # Configure company coordinates
                "pick_up_address": self.company_id.street,
                "pick_up_date": fields.Date.today().strftime('%Y-%m-%d'),
                "pick_up_time": "11:45"  # Configure default pickup time
            },
            "destination_details": {
                "destination_customer_name": invoice.partner_id.name,
                "destination_customer_phone": invoice.partner_id.phone,
                "destination_location": [0, 0],  # Could be configured per address
                "destination_address": invoice.partner_id.street,
                "destination_date": fields.Date.today().strftime('%Y-%m-%d'),
                "destination_time": "14:30"
            },
            "no_of_items": str(len(package_details)),
            "package_details": package_details
        }

        return zajil_data

    def _send_zajil_request(self, data):
        url = 'https://alzajelservice.com/api/create_merchant_order_pdf'
        headers = {
            'auth_key': 'Jkc35282499ZvDs78204815ASUc71226',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception.UserError(f"Error sending request to Zajil: {str(e)}")
# from odoo import models, fields, api
# import requests
# import json
# import logging
# from odoo.exceptions import UserError
# from datetime import datetime

# _logger = logging.getLogger(__name__)


# class StockPicking(models.Model):
#     _inherit = 'stock.picking'

#     alzajel_order_id = fields.Char(string='Alzajel Order ID')
#     alzajel_status = fields.Char(string='Alzajel Status')
#     alzajel_status_code = fields.Integer(string='Status Code')
#     alzajel_driver_name = fields.Char(string='Driver Name')
#     alzajel_driver_phone = fields.Char(string='Driver Phone')
#     alzajel_tracking_url = fields.Char(string='Tracking URL')
#     alzajel_qr_code = fields.Char(string='QR Code URL')
#     alzajel_shipping_cost = fields.Float(string='Shipping Cost')
#     alzajel_date_assigned = fields.Datetime(string='Date Assigned')
#     alzajel_date_delivered = fields.Datetime(string='Date Delivered')
#     alzajel_date_expected = fields.Datetime(string='Expected Delivery Date')
#     alzajel_shipment_type = fields.Selection([
#         ('1', 'Cargo'),
#         ('2', 'Document'),
#         ('3', 'Special Category/Home Appliances')
#     ], string='Shipment Type', default='2')
    
#     alzajel_delivery_type = fields.Selection([
#         ('1', 'Ordinary'),
#         ('2', 'Express')
#     ], string='Delivery Type', default='1')
    
#     alzajel_delivery_fee_by = fields.Selection([
#         ('1', 'Customer'),
#         ('2', 'Merchant')
#     ], string='Delivery Fee Paid By', default='1')
    
#     alzajel_order_notes = fields.Text('Delivery Notes')
#     alzajel_delivery_code = fields.Char('Delivery Code', readonly=True)
#     alzajel_receipt_url = fields.Char('Receipt URL', readonly=True)
#     alzajel_treno_url = fields.Char('Treno URL', readonly=True)
#     alzajel_sender_pdf = fields.Char('Sender PDF', readonly=True)
#     alzajel_live_tracking_url = fields.Char('Live Tracking URL', readonly=True)

#     alzajel_cancellation_charge = fields.Float(string='Cancellation Charge', readonly=True)
#     alzajel_cancelled = fields.Boolean(string='Cancelled in Alzajel', readonly=True)
#     alzajel_cancel_date = fields.Datetime(string='Cancelled Date', readonly=True)


#     def action_create_alzajel_order(self):
#         """Create Alzajel shipping order and get PDF"""
#         self.ensure_one()
        
#         # Get configuration
#         ICP = self.env['ir.config_parameter'].sudo()
#         auth_key = ICP.get_param('alzajel.auth_key')
#         vendor_id = ICP.get_param('alzajel.vendor_id')
#         api_url = ICP.get_param('alzajel.api_url')

#         if not all([auth_key, vendor_id, api_url]):
#             raise UserError('Please configure Alzajel credentials in Settings')

#         # Prepare shipping data
#         shipping_data = self._prepare_alzajel_shipping_data(vendor_id)

#         # Make API request
#         headers = {
#             'auth_key': auth_key,
#             'Content-Type': 'application/json',
#         }

#         try:
#             response = requests.post(
#                 f'{api_url}/create_merchant_order_pdf',
#                 headers=headers,
#                 json=shipping_data
#             )
#             response.raise_for_status()
#             result = response.json()

#             if result.get('success'):
#                 self._handle_alzajel_order_response(result)
#                 return self._show_success_message(result)
#             else:
#                 raise UserError(result.get('message', 'Unknown error occurred'))

#         except requests.exceptions.RequestException as e:
#             raise UserError(f'Error creating Alzajel order: {str(e)}')

#     def _prepare_alzajel_shipping_data(self, vendor_id):
#         """Prepare data for Alzajel API"""
#         company = self.company_id
#         partner = self.partner_id

#         # Calculate total weight and prepare package details
#         package_details = []
#         for move in self.move_ids:
#             package_details.append({
#                 'length': str(move.product_id.length or '30'),
#                 'width': str(move.product_id.width or '30'),
#                 'height': str(move.product_id.height or '30'),
#                 'package_weight': str(move.product_id.weight or '1'),
#                 'package_price': move.sale_line_id.price_unit if move.sale_line_id else 0
#             })

#         # Format pickup and delivery dates
#         pickup_date = fields.Date.today()
#         pickup_time = datetime.now().strftime('%H:%M')
        
#         return {
#             'vendor_id': vendor_id,
#             'order_notes': self.alzajel_order_notes or 'Please deliver at requested time only.',
#             'shipment_type_id': self.alzajel_shipment_type,
#             'Delivery_Fee_pay_By': int(self.alzajel_delivery_fee_by),
#             'delivery_type': self.alzajel_delivery_type,
#             'pick_up_details': {
#                 'pick_up_customer_name': company.name,
#                 'pick_up_customer_phone': company.phone,
#                 'pick_up_location': [
#                     float(company.partner_id.partner_latitude or 0),
#                     float(company.partner_id.partner_longitude or 0)
#                 ],
#                 'pick_up_address': company.partner_id.contact_address,
#                 'pick_up_date': str(pickup_date),
#                 'pick_up_time': pickup_time
#             },
#             'destination_details': {
#                 'destination_customer_name': partner.name,
#                 'destination_customer_phone': partner.phone or partner.mobile,
#                 'destination_location': [
#                     float(partner.partner_latitude or 0),
#                     float(partner.partner_longitude or 0)
#                 ],
#                 'destination_address': partner.contact_address,
#                 'destination_date': str(pickup_date),
#                 'destination_time': pickup_time
#             },
#             'no_of_items': str(len(self.move_ids)),
#             'package_details': package_details
#         }

#     def _handle_alzajel_order_response(self, result):
#         """Handle successful order creation response"""
#         self.write({
#             'alzajel_order_id': result.get('order_id'),
#             'alzajel_status': result.get('order_status'),
#             'alzajel_status_code': result.get('order_status_code'),
#             'alzajel_delivery_code': result.get('delivery_code'),
#             'alzajel_shipping_cost': float(result.get('shipping_quote_total', '0')),
#             'alzajel_receipt_url': result.get('orderReciptUrl'),
#             'alzajel_treno_url': result.get('trenoUrl'),
#             'alzajel_tracking_url': result.get('track_url'),
#             'alzajel_sender_pdf': result.get('senderpdfpath'),
#             'alzajel_live_tracking_url': result.get('liveTrackingUrl')
#         })

#     def _show_success_message(self, result):
#         """Show success message with order details"""
#         return {
#             'type': 'ir.actions.client',
#             'tag': 'display_notification',
#             'params': {
#                 'title': 'Success',
#                 'message': f'Alzajel order created successfully. Order ID: {result.get("order_id")}',
#                 'sticky': False,
#                 'type': 'success',
#             }
#         }
        
#     def action_get_alzajel_status(self):
#         """Manual action to fetch status from Alzajel"""
#         self.ensure_one()
#         if not self.alzajel_order_id:
#             raise UserError('No Alzajel order ID found for this delivery')
        
#         self._fetch_alzajel_status()

#     def _fetch_alzajel_status(self):
#         """Fetch status from Alzajel API"""
#         self.ensure_one()
        
#         if not self.alzajel_order_id:
#             return False

#         # Get configuration
#         ICP = self.env['ir.config_parameter'].sudo()
#         auth_key = ICP.get_param('alzajel.auth_key')
#         vendor_id = ICP.get_param('alzajel.vendor_id')
#         api_url = ICP.get_param('alzajel.api_url')

#         if not all([auth_key, vendor_id, api_url]):
#             _logger.error('Alzajel configuration is incomplete')
#             return False

#         # Prepare API request
#         headers = {
#             'auth_key': auth_key,
#             'Content-Type': 'application/json',
#         }

#         data = {
#             'vendor_id': vendor_id,
#             'order_id': self.alzajel_order_id,
#         }

#         try:
#             response = requests.post(
#                 f'{api_url}/get_order_status',
#                 headers=headers,
#                 json=data
#             )
#             response.raise_for_status()
#             result = response.json()

#             # Update picking with response data
#             self._update_alzajel_data(result)

#         except requests.exceptions.RequestException as e:
#             _logger.error(f'Error fetching Alzajel status: {str(e)}')
#             return False

#         return True

#     def _update_alzajel_data(self, data):
#         """Update picking with Alzajel response data"""
#         self.ensure_one()
        
#         # Convert dates to Odoo datetime format if present
#         date_assigned = fields.Datetime.now()  # Default to now
#         if data.get('date_assigned'):
#             try:
#                 date_assigned = fields.Datetime.from_string(data['date_assigned'])
#             except ValueError:
#                 _logger.warning(f"Could not parse date_assigned: {data['date_assigned']}")

#         vals = {
#             'alzajel_status': data.get('order_status'),
#             'alzajel_status_code': data.get('order_status_code'),
#             'alzajel_driver_name': data.get('driver_name'),
#             'alzajel_driver_phone': data.get('driver_msisdn'),
#             'alzajel_tracking_url': data.get('trackingURl'),
#             'alzajel_qr_code': data.get('qrcode'),
#             'alzajel_shipping_cost': float(data.get('shipping_quote_total', '0')),
#             'alzajel_date_assigned': date_assigned,
#         }

#         self.write(vals)

#     @api.model
#     def _alzajel_cron_update_status(self):
#         """Cron job to update status of active deliveries"""
#         domain = [
#             ('alzajel_order_id', '!=', False),
#             ('state', 'not in', ['done', 'cancel']),
#         ]
#         pickings = self.search(domain)
#         for picking in pickings:
#             picking._fetch_alzajel_status()
            
#     def action_update_alzajel_order(self):
#         """Update existing Alzajel shipping order"""
#         self.ensure_one()
        
#         if not self.alzajel_order_id:
#             raise UserError('No Alzajel order exists for this delivery')

#         # Get configuration
#         ICP = self.env['ir.config_parameter'].sudo()
#         auth_key = ICP.get_param('alzajel.auth_key')
#         vendor_id = ICP.get_param('alzajel.vendor_id')
#         api_url = ICP.get_param('alzajel.api_url')

#         if not all([auth_key, vendor_id, api_url]):
#             raise UserError('Please configure Alzajel credentials in Settings')

#         # Prepare shipping data
#         shipping_data = self._prepare_alzajel_shipping_data(vendor_id)
#         # Add shipment number for update
#         shipping_data['shipmentNo'] = self.alzajel_order_id

#         # Make API request
#         headers = {
#             'auth_key': auth_key,
#             'Content-Type': 'application/json',
#         }

#         try:
#             response = requests.post(
#                 f'{api_url}/update_order',
#                 headers=headers,
#                 json=shipping_data
#             )
#             response.raise_for_status()
#             result = response.json()

#             if result.get('success'):
#                 return self._show_update_success_message(result)
#             else:
#                 raise UserError(result.get('message', 'Unknown error occurred'))

#         except requests.exceptions.RequestException as e:
#             raise UserError(f'Error updating Alzajel order: {str(e)}')

#     def _show_update_success_message(self, result):
#         """Show success message after update"""
#         return {
#             'type': 'ir.actions.client',
#             'tag': 'display_notification',
#             'params': {
#                 'title': 'Success',
#                 'message': result.get('message', 'Order updated successfully'),
#                 'sticky': False,
#                 'type': 'success',
#             }
#         }

#     def open_alzajel_wizard(self):
#         """Open wizard for updating Alzajel order details"""
#         self.ensure_one()
#         return {
#             'name': 'Update Alzajel Shipping',
#             'type': 'ir.actions.act_window',
#             'res_model': 'alzajel.shipping.update.wizard',
#             'view_mode': 'form',
#             'target': 'new',
#             'context': {
#                 'default_picking_id': self.id,
#                 'default_shipment_type': self.alzajel_shipment_type,
#                 'default_delivery_type': self.alzajel_delivery_type,
#                 'default_delivery_fee_by': self.alzajel_delivery_fee_by,
#                 'default_order_notes': self.alzajel_order_notes,
#             }
#         }
        
#     def action_cancel_alzajel_order(self):
#         """Cancel Alzajel shipping order"""
#         self.ensure_one()
        
#         if not self.alzajel_order_id:
#             raise UserError('No Alzajel order exists for this delivery')

#         if self.alzajel_cancelled:
#             raise UserError('This order is already cancelled in Alzajel')

#         # Get configuration
#         ICP = self.env['ir.config_parameter'].sudo()
#         auth_key = ICP.get_param('alzajel.auth_key')
#         api_url = ICP.get_param('alzajel.api_url')

#         if not all([auth_key, api_url]):
#             raise UserError('Please configure Alzajel credentials in Settings')

#         # Prepare cancellation data
#         cancel_data = {
#             'shipmentNo': self.alzajel_order_id
#         }

#         # Make API request
#         headers = {
#             'auth_key': auth_key,
#             'Content-Type': 'application/json',
#         }

#         try:
#             response = requests.post(
#                 f'{api_url}/cancel_order',
#                 headers=headers,
#                 json=cancel_data
#             )
#             response.raise_for_status()
#             result = response.json()

#             if result.get('success'):
#                 # Update local record with cancellation details
#                 self.write({
#                     'alzajel_cancelled': True,
#                     'alzajel_cancel_date': fields.Datetime.now(),
#                     'alzajel_cancellation_charge': float(result.get('order_cancellation_charge', 0)),
#                     'alzajel_status': 'Cancelled',
#                 })
#                 return self._show_cancel_success_message(result)
#             else:
#                 raise UserError(result.get('message', 'Unknown error occurred'))

#         except requests.exceptions.RequestException as e:
#             raise UserError(f'Error cancelling Alzajel order: {str(e)}')

#     def _show_cancel_success_message(self, result):
#         """Show success message after cancellation"""
#         message = f"{result.get('message', 'Order cancelled successfully')}"
#         if result.get('order_cancellation_charge'):
#             message += f"\nCancellation charge: {result.get('order_cancellation_charge')}"
            
#         return {
#             'type': 'ir.actions.client',
#             'tag': 'display_notification',
#             'params': {
#                 'title': 'Success',
#                 'message': message,
#                 'sticky': False,
#                 'type': 'success',
#             }
#         }