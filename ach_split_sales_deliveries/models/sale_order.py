# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round

class SaleOrderLine(models.Model):
    _inherit = 'sale.order'

    create_picking = fields.Boolean(string='Create Picking', compute='_compute_create_picking')

    def _compute_create_picking(self):
        for rec in self:
            check_picking = False
            for line in rec.order_line:
                if line.product_uom_qty_validate < line.product_uom_qty and rec.state in ['done','sale']:
                    check_picking = True
            rec.create_picking = check_picking

    def create_slip_picking(self):
        for order in self:
            order.order_line._action_launch_stock_rule()

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_uom_qty_temp = fields.Float(string="Qty to picking")
    product_uom_qty_validate = fields.Float(string="Qty in picking")
    no_update_qty_temp = fields.Boolean(string='No Update Qty Temp', compute='_compute_update_qty_temp')

    def _compute_update_qty_temp(self):
        for rec in self:
            check_picking = False
            if rec.product_uom_qty_validate < rec.product_uom_qty:
                check_picking = True
            rec.no_update_qty_temp = check_picking

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        if self._context.get("skip_procurement"):
            return True
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        procurements = []
        group = False
        for line in self:
            line = line.with_company(line.company_id)
            if line.product_uom_qty_validate == line.product_uom_qty:
                if (line.product_uom_qty_validate + line.product_uom_qty_temp) > line.product_uom_qty:
                    qty_extra = (line.product_uom_qty_validate + line.product_uom_qty_temp) - line.product_uom_qty
                    raise UserError(_('You cannot generate a delivery with more product than what was sold, of the product %s you are trying to deliver %s %s more than what was sold') % (line.product_id.name, qty_extra, line.product_uom.name))
                continue
            if line.state != 'sale' or not line.product_id.type in ('consu', 'product'):
                continue
            qty = line._get_qty_procurement(previous_product_uom_qty)
            if (line.product_uom_qty_validate + line.product_uom_qty_temp) > line.product_uom_qty:
                qty_extra = (line.product_uom_qty_validate + line.product_uom_qty_temp) - line.product_uom_qty
                raise UserError(_('You cannot generate a delivery with more product than what was sold, of the product %s you are trying to deliver %s %s more than what was sold') % (line.product_id.name, qty_extra, line.product_uom.name))
            group_id = line._get_procurement_group()
            if group == False:
                group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
                line.order_id.procurement_group_id = group_id
                group = True
            else:
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update({'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)
            if line.product_uom_qty_temp == 0:
                continue
            product_qty = line.product_uom_qty_temp
            line_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
            procurements.append(self.env['procurement.group'].Procurement(
                line.product_id, product_qty, procurement_uom,
                line.order_id.partner_shipping_id.property_stock_customer,
                line.product_id.display_name, line.order_id.name, line.order_id.company_id, values))
            line.write({'product_uom_qty_validate':line.product_uom_qty_validate+line.product_uom_qty_temp})
            line.write({'product_uom_qty_temp':0})
        if procurements:
            self.env['procurement.group'].run(procurements)
        orders = self.mapped('order_id')
        for order in orders:
            pickings_to_confirm = order.picking_ids.filtered(lambda p: p.state not in ['cancel', 'done'])
            if pickings_to_confirm:
                # Trigger the Scheduler for Pickings
                pickings_to_confirm.action_confirm()
        return True
    
    """def _action_launch_stock_rule(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        errors = []
        group = False
        for line in self:
            if line.product_uom_qty_validate == line.product_uom_qty:
                if (line.product_uom_qty_validate + line.product_uom_qty_temp) > line.product_uom_qty:
                    qty_extra = (line.product_uom_qty_validate + line.product_uom_qty_temp) - line.product_uom_qty
                    raise UserError(_('You cannot generate a delivery with more product than what was sold, of the product %s you are trying to deliver %s %s more than what was sold') % (line.product_id.name, qty_extra, line.product_uom.name))
                continue
            if line.state not in ['sale','done'] or not line.product_id.type in ('consu','product'):
                continue
            qty = line._get_qty_procurement()
            #Modified
            if (line.product_uom_qty_validate + line.product_uom_qty_temp) > line.product_uom_qty:
                qty_extra = (line.product_uom_qty_validate + line.product_uom_qty_temp) - line.product_uom_qty
                raise UserError(_('You cannot generate a delivery with more product than what was sold, of the product %s you are trying to deliver %s %s more than what was sold') % (line.product_id.name, qty_extra, line.product_uom.name))
            group_id = line.order_id.procurement_group_id
            #Modified
            if group == False:
                group_id = self.env['procurement.group'].create({
                    'name': line.order_id.name, 'move_type': line.order_id.picking_policy,
                    'sale_id': line.order_id.id,
                    'partner_id': line.order_id.partner_shipping_id.id,
                })
                line.order_id.procurement_group_id = group_id
                group = True
            else:
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update({'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)
            values = line._prepare_procurement_values(group_id=group_id)
            ##Modified
            if line.product_uom_qty_temp == 0:
                continue
            product_qty = line.product_uom_qty_temp
            procurement_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            get_param = self.env['ir.config_parameter'].sudo().get_param
            if procurement_uom.id != quant_uom.id and get_param('stock.propagate_uom') != '1':
                product_qty = line.product_uom._compute_quantity(product_qty, quant_uom, rounding_method='HALF-UP')
                procurement_uom = quant_uom
            try:
                self.env['procurement.group'].run(line.product_id, product_qty, procurement_uom, line.order_id.partner_shipping_id.property_stock_customer, line.name, line.order_id.name, values)
                line.write({'product_uom_qty_validate':line.product_uom_qty_validate+line.product_uom_qty_temp})
                line.write({'product_uom_qty_temp':0})
            except UserError as error:
                errors.append(error.name)
        if errors:
            raise UserError('\n'.join(errors))
        return True"""