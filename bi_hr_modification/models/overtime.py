# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import datetime


class EmployeeOverTime(models.Model):
    _name = 'employee.overtime'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'

    name = fields.Char(string='Description', track_visibility='onchange')
    state = fields.Selection(
        [('draft', 'Draft'), ('approved', 'Approved'), ('confirmed', 'Confirmed'), ('cancel', 'Canceled')],
        default='draft', copy=False, track_visibility='onchange')
    employee_id = fields.Many2one('hr.employee', string='Employee', track_visibility='onchange')
    image_medium = fields.Binary(related='employee_id.image_medium')
    expect_sign_out = fields.Float('Expect Sing out', track_visibility='onchange')
    act_sign_out = fields.Float('Actual Sing out', track_visibility='onchange')
    diff = fields.Float('Difference', compute='calculate_diff_hours', store=True, track_visibility='onchange')
    reason = fields.Selection(
        [('none', 'None'), ('business_need', 'Business Need'), ('no_business_need', 'No Business Need')],
        string="Reason", default='none')
    attend_id = fields.Many2one('hr.attendance')
    checkout_date = fields.Datetime('Checkout Date', related='attend_id.check_out', store=True)

    @api.model
    def create(self, values):
        res = super(EmployeeOverTime, self).create(values)
        if res.employee_id.parent_id.address_home_id:
            ovt = str(datetime.timedelta(hours=res.diff)).rsplit(':', 1)[0]

            mail_data = {'subject': 'New Overtime Created ',
                         'body_html': 'Dear ' + res.employee_id.parent_id.name + ',<br/>' +
                                      'New overtime record has been created to employee ' + res.employee_id.name + " , Overtime hours " + ovt + "<br/>",
                         'recipient_ids': [(6, 0, [res.employee_id.parent_id.address_home_id.id])],
                         'author_id': self.env.ref('base.partner_admin').id,
                         }

            mail = self.env['mail.mail'].create(mail_data)
            mail.send()
        return res

    @api.multi
    @api.depends('expect_sign_out', 'act_sign_out', 'employee_id')
    def calculate_diff_hours(self):
        for val in self:
            val.diff = val.act_sign_out - val.expect_sign_out

    @api.multi
    def action_confirmed(self):
        for rec in self:
            if rec.reason == 'none':
                raise ValidationError(_('You must set reason to confirm !'))
            rec.state = 'confirmed'

    @api.multi
    def action_approve(self):
        for rec in self:
            rec.state = 'approved'

    @api.multi
    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'
