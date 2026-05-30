# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
import datetime

# ==========================================
# PHẦN 1: DANH MỤC & THƯƠNG HIỆU (CỦA BẠN - ĐÃ CHUẨN HÓA THEO BT.DOCX)
# ==========================================
class equipment_category(osv.osv):
    _name = 'equipment.category'
    _columns = {
        'code': fields.char(u'Mã danh mục', size=32, required=True),
        'name': fields.char(u'Tên loại', size=64, required=True),
    }
    
    # RBTV 3: Ràng buộc duy nhất
    _sql_constraints = [
        ('code_uniq', 'unique(code)', u'Mã danh mục này đã tồn tại!'),
        ('name_uniq', 'unique(name)', u'Tên danh mục này đã tồn tại!')
    ]

    def _check_name_length(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            if record.name and len(record.name.strip()) < 2:
                return False
        return True
        
    _constraints = [
        (_check_name_length, u'Lỗi: Tên danh mục phải có ít nhất 2 ký tự!', ['name'])
    ]

class equipment_brand(osv.osv):
    _name = 'equipment.brand'
    _columns = {
        'name': fields.char(u'Tên thương hiệu', size=64, required=True),
        'logo': fields.binary(u'Logo'),
        'hotline': fields.char(u'Hotline Hãng', size=32),
        'email': fields.char(u'Email', size=64),
    }
    
    # RBTV 3: Ràng buộc duy nhất (Đúng text yêu cầu trong Word)
    _sql_constraints = [
        ('name_uniq', 'unique(name)', u'Constraint Error: Tên thương hiệu đã tồn tại!') 
    ]

    def _check_brand_name_length(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            if record.name and len(record.name.strip()) < 2:
                return False
        return True

    def _check_hotline_numeric(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            if record.hotline:
                cleaned_hotline = record.hotline.replace(' ', '').replace('-', '').replace('.', '')
                if not cleaned_hotline.isdigit():
                    return False
        return True
        
    # RBTV 5: Ràng buộc độ dài (Đúng text yêu cầu trong Word)
    _constraints = [
        (_check_brand_name_length, u'Tên thương hiệu phải có ít nhất 2 ký tự!', ['name']),
        (_check_hotline_numeric, u'Lỗi: Hotline hãng chỉ được phép nhập số!', ['hotline'])
    ]

# ==========================================
# PHẦN 2: NHÀ CUNG CẤP (CỦA BẠN)
# ==========================================
class equipment_supplier(osv.osv):
    _name = 'equipment.supplier'
    _columns = {
        'code': fields.char(u'Mã Nhà cung cấp', size=32, required=True),
        'name': fields.char(u'Tên Nhà cung cấp', size=128, required=True),
        'phone': fields.char(u'Số điện thoại', size=32),
        'email': fields.char(u'Email', size=64),
        'address': fields.text(u'Địa chỉ văn phòng'),
        'tax_code': fields.char(u'Mã số thuế', size=32),
        'representative': fields.char(u'Người đại diện thương mại', size=64),
    }
    _sql_constraints = [
        ('code_uniq', 'unique(code)', u'Lỗi: Mã nhà cung cấp đã tồn tại!'),
        ('name_uniq', 'unique(name)', u'Lỗi: Tên nhà cung cấp đã tồn tại!')
    ]

# ==========================================
# PHẦN 3: KHO HÀNG (CỦA BẠN - ĐÃ CHUẨN HÓA THEO BT.DOCX)
# ==========================================
class equipment_inventory(osv.osv):
    _name = 'equipment.inventory'
    _columns = {
        'name': fields.char(u'Số phiếu', readonly=True), 
        'type': fields.selection([('in', u'Nhập kho'), ('out', u'Xuất kho')], u'Loại phiếu', required=True),
        'reason': fields.selection([('purchase', u'Nhập từ NCC'), ('sale', u'Bán hàng'), ('warranty', u'Xuất bảo hành'), ('scrap', u'Hủy hàng')], u'Mục đích', required=True),
        # RBTV 7: Chặn xóa dữ liệu có liên kết (Restrict OnDelete)
        'product_id': fields.many2one('equipment.product', u'Sản phẩm', required=True, ondelete='restrict'), 
        'quantity': fields.float(u'Số lượng', required=True),
        'price_unit': fields.float(u'Giá ghi sổ (Nhập/Xuất)'),
        'date': fields.datetime(u'Ngày thực hiện', required=True),
        'user_id': fields.many2one('res.users', u'Người lập phiếu', readonly=True), 
        'note': fields.char(u'Ghi chú'),
        'state': fields.selection([('draft', u'Nháp'), ('done', u'Đã xác nhận'), ('cancel', u'Đã hủy')], u'Trạng thái', readonly=True),
    }
    
    # RBTV 10: Tự động gán giờ hiện tại và tài khoản người dùng
    _defaults = {
        'date': lambda *a: fields.datetime.now(), 
        'state': 'draft', 
        'reason': 'sale',
        'user_id': lambda obj, cr, uid, context: uid
    }

    def create(self, cr, uid, vals, context=None):
        # RBTV 1: Số lượng giao dịch (Đúng text yêu cầu trong Word)
        if vals.get('quantity', 0) <= 0:
            raise osv.except_osv(_(u'OpenERP Warning'), _(u'Số lượng giao dịch phải lớn hơn 0!')) 

        # RBTV 8: Logic Ngày giờ (Đúng text yêu cầu trong Word)
        if vals.get('date'):
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if vals.get('date') > current_time:
                raise osv.except_osv(_(u'Lỗi ngày tháng'), _(u'Ngày giao dịch không thể lớn hơn ngày hiện tại!'))

        # RBTV 9: Xuất kho bắt buộc nhập ghi chú (Đúng text yêu cầu trong Word)
        if vals.get('type') == 'out' and not vals.get('note'):
            raise osv.except_osv(_(u'Cảnh báo'), _(u'Vui lòng nhập lý do (Ghi chú) khi thực hiện Xuất kho thiết bị!'))

        # RBTV 1: Kiểm tra tồn kho (Đúng text yêu cầu trong Word)
        if vals.get('type') == 'out' and vals.get('product_id'):
            prod_obj = self.pool.get('equipment.product')
            product = prod_obj.browse(cr, uid, vals['product_id'], context=context)
            if vals.get('quantity') > product.qty_available:
                raise osv.except_osv(_(u'Lỗi tồn kho'), _(u'Số lượng tồn kho không đủ để xuất!'))

        if not vals.get('name'):
            prefix = 'PN' if vals.get('type') == 'in' else 'PX'
            vals['name'] = '%s/%s' % (prefix, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
        return super(equipment_inventory, self).create(cr, uid, vals, context=context)

    def action_done(self, cr, uid, ids, context=None):
        prod_obj = self.pool.get('equipment.product')
        for inv in self.browse(cr, uid, ids, context=context):
            if inv.state == 'done': continue
            change = inv.quantity if inv.type == 'in' else -inv.quantity
            new_qty = inv.product_id.qty_available + change
            state = 'out_of_stock' if new_qty <= 0 else 'in_stock'
            prod_obj.write(cr, uid, [inv.product_id.id], {'qty_available': new_qty, 'state': state})
            self.write(cr, uid, [inv.id], {'state': 'done'})
        return True


# ==========================================
# CÁC PHẦN CỦA NHÓM: GIỮ NGUYÊN 100% NHƯ BẠN YÊU CẦU (TRÁNH LỖI VIEW)
# ==========================================

class equipment_product(osv.osv):
    _name = 'equipment.product'
    _columns = {
        'default_code': fields.char(u'Mã SKU', size=64),
        'name': fields.char(u'Tên thiết bị/Linh kiện', size=128, required=True),
        # Thêm RBTV 4 (Restrict on Delete) cho category_id liên quan đến phần Danh Mục của bạn
        'category_id': fields.many2one('equipment.category', u'Loại sản phẩm', required=True, ondelete='restrict'),
        'brand_id': fields.many2one('equipment.brand', u'Thương hiệu (Hãng/NCC)'),
        'image': fields.binary(u'Ảnh sản phẩm'),
        'warranty': fields.integer(u'Bảo hành (tháng)'),
        'qty_available': fields.float(u'Số lượng tồn', readonly=True),
        'standard_price': fields.float(u'Giá nhập'),
        'price': fields.float(u'Giá bán'),
        'state': fields.selection([('in_stock', u'Còn hàng'), ('out_of_stock', u'Hết hàng'), ('obsolete', u'Ngừng kinh doanh')], u'Trạng thái'),
        'specifications': fields.text(u'Thông số kỹ thuật'),
    }
    _defaults = {'qty_available': 0.0, 'state': 'in_stock', 'standard_price': 0.0, 'price': 0.0}

class equipment_partner(osv.osv):
    _name = 'equipment.partner'
    _columns = {
        'name': fields.char(u'Tên đối tác', size=128, required=True),
        'phone': fields.char(u'SĐT', size=32),
        'email': fields.char(u'Email', size=64),
        'address': fields.text(u'Địa chỉ'),
        'is_customer': fields.boolean(u'Là Khách hàng'),
        'is_supplier': fields.boolean(u'Là Nhà cung cấp'),
        'membership_tier': fields.selection([('bronze', u'Đồng'), ('silver', u'Bạc'), ('gold', u'Vàng'), ('diamond', u'Kim Cương')], u'Hạng thành viên'),
        'points': fields.integer(u'Điểm tích lũy'),
    }
    _defaults = {'is_customer': True, 'is_supplier': False, 'membership_tier': 'bronze', 'points': 0}

    _sql_constraints = [
        ('check_points', 'CHECK(points >= 0)', u'Lỗi: Điểm tích lũy không được phép âm!')
    ]

    def _check_phone(self, cr, uid, ids, context=None):
        for partner in self.browse(cr, uid, ids, context=context):
            if partner.phone and len(partner.phone) < 8:
                return False
        return True

    _constraints = [
        (_check_phone, u'Lỗi: Số điện thoại không hợp lệ (phải có ít nhất 8 số)!', ['phone'])
    ]

class equipment_order(osv.osv):
    _name = 'equipment.order'
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = sum(line.price_subtotal for line in order.line_ids)
        return res

    _columns = {
        'name': fields.char(u'Mã Hóa đơn', size=64, readonly=True),
        'partner_id': fields.many2one('equipment.partner', u'Khách hàng/NCC', required=True),
        'user_id': fields.many2one('res.users', u'Nhân viên phụ trách'),
        'order_date': fields.datetime(u'Ngày tạo', required=True),
        'order_type': fields.selection([('sale', u'Bán hàng'), ('purchase', u'Nhập hàng')], u'Loại đơn', required=True),
        'payment_status': fields.selection([('unpaid', u'Chưa thanh toán'), ('paid', u'Đã thanh toán')], u'Thanh toán'),
        'state': fields.selection([('draft', u'Nháp'), ('confirmed', u'Đã xác nhận'), ('done', u'Hoàn thành')], u'Trạng thái', readonly=True),
        'line_ids': fields.one2many('equipment.order.line', 'order_id', u'Chi tiết Hóa đơn'),
        'total_amount': fields.function(_amount_all, type='float', string=u'Tổng tiền'),
    }
    _defaults = {
        'state': 'draft', 
        'payment_status': 'unpaid',
        'order_date': lambda *a: fields.datetime.now(), 
        'order_type': 'sale',
        'user_id': lambda obj, cr, uid, context: uid,
    }

    def create(self, cr, uid, vals, context=None):
        if not vals.get('name'):
            prefix = 'HD' if vals.get('order_type') == 'sale' else 'PO'
            vals['name'] = '%s/%s' % (prefix, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
        return super(equipment_order, self).create(cr, uid, vals, context=context)

    def action_done(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context=context):
            if order.order_type == 'sale' and order.partner_id:
                new_points = order.partner_id.points + int(order.total_amount / 100000)
                self.pool.get('equipment.partner').write(cr, uid, [order.partner_id.id], {'points': new_points})
        return self.write(cr, uid, ids, {'state': 'done', 'payment_status': 'paid'})

class equipment_order_line(osv.osv):
    _name = 'equipment.order.line'
    def _calc_subtotal(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.quantity * line.price_unit
        return res
        
    def onchange_product_id(self, cr, uid, ids, product_id, context=None):
        res = {'value': {}}
        if context is None:
            context = {}
        if product_id:
            product = self.pool.get('equipment.product').browse(cr, uid, product_id, context=context)
            order_type = context.get('default_order_type', 'sale')
            res['value']['price_unit'] = product.price if order_type == 'sale' else product.standard_price
        return res
        
    _columns = {
        'order_id': fields.many2one('equipment.order', u'Đơn hàng', ondelete='cascade'),
        'product_id': fields.many2one('equipment.product', u'Thiết bị', required=True),
        'quantity': fields.float(u'Số lượng', required=True),
        'price_unit': fields.float(u'Đơn giá', required=True),
        'price_subtotal': fields.function(_calc_subtotal, type='float', string=u'Thành tiền'),
    }
    _defaults = {'quantity': 1.0, 'price_unit': 0.0}

class equipment_warranty(osv.osv):
    _name = 'equipment.warranty'
    _columns = {
        'name': fields.char(u'Số Serial (S/N)', size=64, required=True),
        'product_id': fields.many2one('equipment.product', u'Sản phẩm', required=True),
        'partner_id': fields.many2one('equipment.partner', u'Khách hàng'),
        'order_id': fields.many2one('equipment.order', u'Hóa đơn mua'),
        'purchase_date': fields.date(u'Ngày mua'),
        'end_date': fields.date(u'Ngày hết hạn BH'),
        'state': fields.selection([('valid', u'Còn bảo hành'), ('expired', u'Hết bảo hành')], u'Trạng thái'),
    }