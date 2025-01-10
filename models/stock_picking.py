import requests
import json
import logging
from odoo import models, fields, exceptions, _, api
from datetime import datetime

_logger = logging.getLogger(__name__)


zajilauthkey = "ZLa41648Wvkl2402501fSZx23797gSub" 
class StockPicking(models.Model):
    _inherit = 'stock.picking'

    zajil_delivery_code = fields.Char(string='Zajil Delivery Code', readonly=True)
    zajil_tracking_url = fields.Char(string='Zajil Tracking URL', readonly=True)
    zajil_receipt_url = fields.Char(string='Zajil Receipt URL', readonly=True)
    zajil_order_state = fields.Selection([
        ('created', 'Created'),
        ('cancelled', 'Cancelled')
    ], string='Zajil Order State', copy=False)
    
    def action_cancel_zajil_shipment(self):
        """Cancel Zajil shipment"""
        self.ensure_one()

        if not self.carrier_tracking_ref:
            raise exceptions.UserError(_("No Zajil shipment found to cancel."))

        try:
            _logger.info("Attempting to cancel Zajil shipment: %s", self.carrier_tracking_ref)

            # Prepare cancel request
            url = 'https://alzajelservice.com/api/cancel_order'
            headers = {
                'auth_key': zajilauthkey,
                'Content-Type': 'application/json'
            }
            data = {
                'shipmentNo': self.carrier_tracking_ref
            }

            _logger.info("Sending cancel request to Zajil API - Data: %s", data)

            response = requests.post(url, json=data, headers=headers)
            _logger.info("Zajil API Cancel Response Status Code: %s", response.status_code)
            _logger.info("Zajil API Cancel Response Content: %s", response.text)

            response_data = response.json()

            if response_data.get('success'):
                # Update picking status
                self.write({
                    'zajil_order_state': 'cancelled'
                })

                # Create message in chatter
                cancel_msg = _("""Zajil Shipment Cancelled Successfully
Order ID: %s
Message: %s
Cancellation Charge: %s""") % (
                    self.carrier_tracking_ref,
                    response_data.get('message'),
                    response_data.get('order_cancellation_charge', 0)
                )
                self.message_post(body=cancel_msg)

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _("Success"),
                        'message': _("Zajil shipment cancelled successfully."),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                error_msg = response_data.get('message', 'Unknown error')
                _logger.error("Failed to cancel Zajil shipment: %s", error_msg)
                raise exceptions.UserError(_(f"Failed to cancel Zajil shipment: {error_msg}"))

        except requests.exceptions.RequestException as e:
            _logger.error("Error in Zajil API cancel request: %s", str(e), exc_info=True)
            raise exceptions.UserError(_(f"Error communicating with Zajil API: {str(e)}"))
        except Exception as e:
            _logger.error("Error cancelling Zajil shipment: %s", str(e), exc_info=True)
            raise exceptions.UserError(_(f"Error cancelling Zajil shipment: {str(e)}"))

    def process_sajil_delivery(self):
        try:
            _logger.info("Starting Zajil delivery process for picking ID: %s", self.id)
            
            # Prepare Zajil shipment data
            zajil_data = self._prepare_zajil_data()
            _logger.info("Prepared Zajil data: %s", json.dumps(zajil_data, indent=2))

            # Send request to Zajil API
            response = self._send_zajil_request(zajil_data)
            _logger.info("Received Zajil API response: %s", json.dumps(response, indent=2))

            if response.get('success'):
                # Update picking with Zajil tracking information
                update_vals = {
                    'carrier_tracking_ref': response.get('order_id'),
                    'zajil_delivery_code': response.get('delivery_code'),
                    'zajil_tracking_url': response.get('track_url'),
                    'zajil_receipt_url': response.get('orderReciptUrl')
                }
                _logger.info("Updating picking with values: %s", update_vals)
                
                self.write(update_vals)
                tracking_msg = _("""Zajil Delivery Created Successfully
                    Order ID: %s
                    Delivery Code: %s
                    Status: %s
                    Tracking URL: %s
                    Receipt URL: %s""") % (
                    response.get('order_id'),
                    response.get('delivery_code'),
                    response.get('order_status'),
                    response.get('track_url'),
                    response.get('orderReciptUrl')
                )
                self.message_post(body=tracking_msg)

                # Call parent validation
                res = super(StockPicking, self).button_validate()
                _logger.info("Successfully validated picking")

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _("Success"),
                        'message': _("""Shipment created successfully!
                                                                        Order ID: %s
                                                                        Tracking Code: %s
                                                                        Status: %s""") % (
                            response.get('order_id'),
                            response.get('delivery_code'),
                            response.get('order_status')
                        ),
                        'type': 'success',
                        'sticky': False,
                        'next': {
                            'type': 'ir.actions.act_url',
                            'url': response.get('track_url'),
                            'target': 'new'
                        }
                    }
                }
            else:
                error_msg = response.get('message', 'Unknown error')
                _logger.error("Failed to create Zajil shipment: %s", error_msg)
                raise exceptions.UserError(_(f"Failed to create Zajil shipment: {error_msg}"))
        except Exception as e:
            _logger.error("Error in process_sajil_delivery: %s", str(e), exc_info=True)
            raise exceptions.UserError(_(f"Error processing Zajil delivery: {str(e)}"))

    
    def action_view_zajil_tracking(self):
        self.ensure_one()
        if self.zajil_tracking_url:
            return {
                'type': 'ir.actions.act_url',
                'url': self.zajil_tracking_url,
                'target': 'new'
            }
        raise exceptions.UserError(_("No tracking URL available"))
    
    def _prepare_zajil_data(self):
        try:
            _logger.info("Preparing Zajil data for picking ID: %s", self.id)

            # Get related sale order or invoice
            invoice = self.env['account.move'].sudo().search([
                ('invoice_origin', '=', self.origin)
            ], limit=1)

            if not invoice:
                _logger.error("No invoice found for origin: %s", self.origin)
                raise exceptions.UserError('No invoice found')

            # Create a mapping of product_id to price from invoice lines
            product_prices = {
                line.product_id.id: line.price_unit
                for line in invoice.invoice_line_ids
            }

            # Prepare package details
            package_details = []
            for move_line in self.move_line_ids:
                price = product_prices.get(move_line.product_id.id, 0)
                package_detail = {
                    "length": "30",
                    "width": "30",
                    "height": "30",
                    "package_weight": str(move_line.product_id.weight or 1),
                    "package_price": price
                }
                _logger.info("Created package detail: %s for product: %s",
                            package_detail, move_line.product_id.name)
                package_details.append(package_detail)

          
            vendor_id = "6773e6a250b1b88c1b701857"
            # pickup_lat = float(IrConfigParam.get_param('zajil.pickup_lat', '33.33332'))
            # pickup_lng = float(IrConfigParam.get_param('zajil.pickup_lng', '44.45220'))

            # Format phone numbers
            company_phone = self._format_phone_number(self.company_id.phone)
            customer_phone = self._format_phone_number(invoice.partner_id.phone)
            if ( len(customer_phone) ==0 ):
                customer_phone = self._format_phone_number(invoice.partner_id.mobile)
                if(len(customer_phone) ==0 ):
                    raise exceptions.UserError(_("Error phone number is not true"))

            # Get destination coordinates if available
            destination_lat = invoice.partner_id.partner_latitude or 33.32208
            destination_lng = invoice.partner_id.partner_longitude or 44.35281

            zajil_data = {
                "vendor_id": vendor_id,
                "order_notes": "test",#invoice.narration or "",
                "shipment_type_id": "2",
                "Delivery_Fee_pay_By": 1,
                "delivery_type": "1",
                "pick_up_details": {
                    "pick_up_customer_name": self.company_id.name,
                    "pick_up_customer_phone": self._format_phone_number(self.company_id.phone),
                    "pick_up_location":[33.323097,44.32587],
                    "pick_up_address": self.company_id.street or "Default Address",
                    "pick_up_date": fields.Date.today().strftime('%Y-%m-%d'),
                    "pick_up_time": datetime.now().strftime('%H:%M')
                },
                "destination_details": {
                    "destination_customer_name": invoice.partner_id.name,
                    "destination_customer_phone": customer_phone,
                    "destination_location":[33.323097,44.32587],
                    "destination_address": f"{invoice.partner_id.street or ''} {invoice.partner_id.street2 or ''}".strip(),
                    "destination_date": fields.Date.today().strftime('%Y-%m-%d'),
                    "destination_time": datetime.now().strftime('%H:%M')
                },
                "no_of_items": str(len(package_details)),
                "package_details": package_details
            }

            _logger.info("Successfully prepared Zajil data: %s", json.dumps(zajil_data, indent=2))
            return zajil_data

        except Exception as e:
            _logger.error("Error preparing Zajil data: %s", str(e), exc_info=True)
            raise exceptions.UserError(_(f"Error preparing shipment data: {str(e)}"))
    

    def _send_zajil_request(self, data):
        try:
            url = 'https://alzajelservice.com/api/create_merchant_order_pdf'
            headers = {
                'auth_key':zajilauthkey,
                'Content-Type': 'application/json'
            }

            _logger.info("Sending request to Zajil API - URL: %s", url)
            _logger.info("Request Headers: %s", headers)
            _logger.info("Request Data: %s", json.dumps(data, indent=2))

            response = requests.post(url, json=data, headers=headers)
            _logger.info("Zajil API Response Status Code: %s", response.status_code)
            _logger.info("Zajil API Response Content: %s", response.text)

            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            _logger.error("Error in Zajil API request: %s", str(e), exc_info=True)
            raise exceptions.UserError(_(f"Error communicating with Zajil API: {str(e)}"))

    def _format_phone_number(self, phone):
        """Format phone number to required format"""
        if not phone:
            return ""

        # Remove any non-digit characters
        phone = ''.join(filter(str.isdigit, phone))

        # Remove leading zeros
        phone = phone.lstrip('0')

        # Remove country code if present
        if phone.startswith('964'):
            phone = phone[3:]
        elif phone.startswith('00964'):
            phone = phone[5:]

        # Ensure the number is at least 9 digits
        if len(phone) < 9:
            raise exceptions.UserError(_("Phone number must be at least 9 digits long"))

        return phone