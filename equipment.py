# -*- coding: utf-8 -*-
from openerp.osv import fields, osv

class equipment_category(osv.osv):
    _name = 'equipment.category'
    _columns = {
        'name': fields.char('Tên loại', size=64, required=True),
        'description': fields.text('Mô tả'),
    }
    equipment_category()


class equipment_brand(osv.osv):
    _name = 'equipment.brand'
    _columns = {
        'name': fields.char('Tên thương hiệu', size=64, required=True),
        'country': fields.char('Quốc gia'),
    }
    equipment_brand()


class equipment_product(osv.osv):
    _name = 'equipment.product'
    _columns = {
        'name': fields.char('Tên thiết bị', size=128, required=True),
        'category_id': fields.many2one('equipment.category', 'Loại sản phẩm', required=True),
        'brand_id': fields.many2one('equipment.brand', 'Thương hiệu'),
        'qty_available': fields.float('Số lượng tồn', readonly=True),
        'price': fields.float('Đơn giá'),
        'specifications': fields.text('Thông số kỹ thuật'),
    }
    equipment_product()


class equipment_inventory(osv.osv):
    _name = 'equipment.inventory'
    _columns = {
        'product_id': fields.many2one('equipment.product', 'Thiết bị', required=True),
        'type': fields.selection([('in', 'Nhập kho'), ('out', 'Xuất kho')], 'Loại', required=True),
        'quantity': fields.float('Số lượng', required=True),
        'date': fields.datetime('Ngày thực hiện'),
        'note': fields.char('Ghi chú'),
    }
    _defaults = {'date': lambda *a: fields.datetime.now()}
    equipment_inventory()

    def create(self, cr, uid, vals, context=None):
        res_id = super(equipment_inventory, self).create(cr, uid, vals, context=context)
        inv = self.browse(cr, uid, res_id, context=context)
        prod_obj = self.pool.get('equipment.product')
        change = inv.quantity if inv.type == 'in' else -inv.quantity
        new_qty = inv.product_id.qty_available + change
        prod_obj.write(cr, uid, [inv.product_id.id], {'qty_available': new_qty})
        return res_id