# -*- coding: utf-8 -*-
from openerp.osv import fields, osv

class equipment_category(osv.osv):
    _name = 'equipment.category'
    _columns = {
        'name': fields.char('Tên loại', size=64, required=True),
        'description': fields.text('Mô tả'),
    }

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

# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _  # Thêm thư viện này để hiển thị thông báo lỗi

# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
import datetime

# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
import datetime

# ==========================================
# PHẦN 3: QUẢN LÝ THƯƠNG HIỆU
# ==========================================
class equipment_brand(osv.osv):
    _name = 'equipment.brand'
    _columns = {
        'name': fields.char(u'Tên thương hiệu', size=64, required=True),
        'country': fields.char(u'Quốc gia'),
        'logo': fields.binary(u'Logo'), 
    }
    
    _sql_constraints = [
        ('name_uniq', 'unique (name)', u'Constraint Error: Tên thương hiệu đã tồn tại!')
    ]

    def _check_name_length(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            if record.name and len(record.name.strip()) < 2:
                return False
        return True
        
    _constraints = [
        (_check_name_length, u'Tên thương hiệu phải có ít nhất 2 ký tự!', ['name'])
    ]

# ==========================================
# PHẦN 4: QUẢN LÝ KHO
# ==========================================
class equipment_inventory(osv.osv):
    _name = 'equipment.inventory'
    _columns = {
        'name': fields.char(u'Mã số phiếu', readonly=True),
        'user_id': fields.many2one('res.users', u'Người lập phiếu', readonly=True),
        'state': fields.selection([('draft', u'Nháp'), ('done', u'Đã xác nhận'), ('cancel', u'Đã hủy')], u'Trạng thái', readonly=True),
        
        'product_id': fields.many2one('equipment.product', u'Thiết bị', required=True, ondelete='restrict'), 
        'type': fields.selection([('in', u'Nhập kho'), ('out', u'Xuất kho')], u'Loại', required=True),
        'quantity': fields.float(u'Số lượng', required=True),
        'date': fields.datetime(u'Ngày thực hiện', required=True),
        'note': fields.char(u'Ghi chú'),
    }
    
    _defaults = {
        'date': lambda *a: fields.datetime.now(),
        'state': 'draft',
        'user_id': lambda obj, cr, uid, context: uid,
    }

    def create(self, cr, uid, vals, context=None):
        if vals.get('quantity', 0) <= 0:
            raise osv.except_osv(_(u'Cảnh báo'), _(u'Số lượng giao dịch phải lớn hơn 0!'))

        if vals.get('date'):
            current_time = fields.datetime.now()
            if vals['date'] > current_time:
                raise osv.except_osv(_(u'Lỗi ngày tháng'), _(u'Ngày giao dịch không thể lớn hơn ngày hiện tại!'))

        if vals.get('type') == 'out' and not vals.get('note'):
            raise osv.except_osv(_(u'Cảnh báo'), _(u'Vui lòng nhập lý do (Ghi chú) khi thực hiện Xuất kho thiết bị!'))

        if vals.get('type') == 'out' and vals.get('product_id'):
            prod_obj = self.pool.get('equipment.product')
            product = prod_obj.browse(cr, uid, vals['product_id'], context=context)
            if vals.get('quantity') > product.qty_available:
                raise osv.except_osv(_(u'Lỗi tồn kho'), _(u'Số lượng tồn kho không đủ để xuất!'))

        if not vals.get('name'):
            prefix = 'IN' if vals.get('type') == 'in' else 'OUT'
            vals['name'] = '%s/%s' % (prefix, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))

        return super(equipment_inventory, self).create(cr, uid, vals, context=context)

    def action_done(self, cr, uid, ids, context=None):
        prod_obj = self.pool.get('equipment.product')
        for inv in self.browse(cr, uid, ids, context=context):
            if inv.state == 'done':
                continue
            
            change = inv.quantity if inv.type == 'in' else -inv.quantity
            new_qty = inv.product_id.qty_available + change
            
            prod_obj.write(cr, uid, [inv.product_id.id], {'qty_available': new_qty})
            self.write(cr, uid, [inv.id], {'state': 'done'})
        return True