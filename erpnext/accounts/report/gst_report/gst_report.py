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
	gst_types = frappe.get_all("GST Types",fields=["name"],order_by="name")
	
	for d in gst_types:
		total_out = frappe.db.sql("""select cs_gst_type, ifnull(sum(output_sales_value),0) from `tabGST Details` where gst_type ='-GST Output' and cs_gst_type='%s' %s """%(d['name'],conditions),as_list=1)
		for row in total_out:
			if row[0]!=None:
				data.append([row[0],row[1]])


	total_out_value = frappe.db.sql("""select ifnull(sum(output_sales_value),0),ifnull(sum(output_gst_collected),0) from `tabGST Details` where gst_type = '-GST Output' %s """%(conditions),as_list=1)
	if total_out_value:
		data.append(['Total value of Sales Output',total_out_value[0][0]])


	taxable_purchase = frappe.db.sql("""select ifnull(sum(input_purchase_value),0),ifnull(sum(input_gst_paid),0) from `tabGST Details` where gst_type = '-GST Input' %s """%(conditions),as_list=1)
	if taxable_purchase:
		data.append(['Total value of Taxable Purchases',taxable_purchase[0][0]])

	if total_out_value:
		data.append(['Output Tax Due',total_out_value[0][1]])

	if taxable_purchase:
		data.append(['Less: Input tax and refunds claimed',taxable_purchase[0][1]])

	if total_out_value and taxable_purchase:
		data.append(['<b>'+'Equals: Net GST to be paid to/(refunded by) IRAS'+'</b>',total_out_value[0][1] - taxable_purchase[0][1]])

	data.append([])

	data.append(['Revenue for the accounting period',total_out_value[0][0]])
	
	return data

def get_conditions(filters):
	conditions = ""
	if filters.get("from_date"): conditions += "and date between '%s'" %filters["from_date"]
	if filters.get("to_date"): conditions += " and '%s'" %filters["to_date"]

	return conditions
