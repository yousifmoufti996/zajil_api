# -*- coding: utf-8 -*-
# from odoo import http


# class ZajilApi(http.Controller):
#     @http.route('/zajil_api/zajil_api', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/zajil_api/zajil_api/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('zajil_api.listing', {
#             'root': '/zajil_api/zajil_api',
#             'objects': http.request.env['zajil_api.zajil_api'].search([]),
#         })

#     @http.route('/zajil_api/zajil_api/objects/<model("zajil_api.zajil_api"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('zajil_api.object', {
#             'object': obj
#         })

