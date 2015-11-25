# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, getdate, cstr
from frappe import _
from datetime import date, timedelta

def execute(filters=None):
	columns, data = [], []
	validate_filters(filters)
	columns = get_columns()
	data = get_result(filters)

	return columns, data

def validate_filters(filters):
	if filters.from_date > filters.to_date:
		frappe.throw(_("To Date must be greater than From Date"))

def get_columns():
	return [_("") + ":data:350", _("Total Values") + ":Float:120"]

def get_result(filters):
	data = []
	conditions = get_conditions(filters)
	total_values = frappe.db.sql("""select sum(ifnull(output_sales_value, 0)), sum(ifnull(input_purchase_value, 0)), 
		sum(ifnull(output_gst_collected, 0)), sum(ifnull(input_gst_paid, 0)) from `tabGST Details` %s""" %conditions,as_list=1)
	if total_values:
		gst_total = total_values[0][2] - total_values[0][3]

	data = [['Total value of standard-rated supplies',total_values[0][0]], ['Total value of zero-rated supplies',0.0],
			['Total value of exempt supplies',0.0], ['Total value',total_values[0][0]], 
			['Total value of taxable purchases',total_values[0][1]], 
			['Output tax due',total_values[0][2]], ['Input tax and refunds claimed',total_values[0][3]], 
			['Net GST to be paid to IRAS',gst_total], ['Revenue for the accounting Period',total_values[0][0]]]
		
	return data

def get_conditions(filters):
	conditions = ""
	if filters.get("from_date"): conditions += " where date between '%s'" %filters["from_date"]
	if filters.get("to_date"): conditions += " and '%s'" %filters["to_date"]

	return conditions
