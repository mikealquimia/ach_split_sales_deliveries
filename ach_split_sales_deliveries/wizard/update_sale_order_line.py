# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round

class UpdateSaleOrderLine(models.TransientModel):
    _name = 'update.sale.order.line'
    _description = 'Set Qty Sale Order Line'

    name = fields.Char(string='name')
    order_id = fields.Many2one('sale.order', string='Order')
    order_line = fields.One2many('sale.order.line', 'order_id', string='Order Lines', related="order_id.order_line", readonly=False)

    @api.multi
    def set_order_line(self):
        return self.order_id.create_slip_picking()