# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, getdate, cstr
from frappe import _
from datetime import date, timedelta

def execute(filters=None):
	columns, res = [], []
	validate_filters(filters)
	columns = get_columns()
	res = get_result(filters)

	return columns , res

def validate_filters(filters):
	if filters.from_date > filters.to_date:
		frappe.throw(_("To Date must be greater than From Date"))

def get_columns():
	return [_("Customer Name") + ":Link/Customer:180",_("Date") + ":Date:120", _("ID") + ":Link/Sales Invoice:120", 
		_("Rate") + ":Float:120", _("Sales Value") + ":Float:120", _("GST Collected") + ":Float:150",
		_("Gross") + ":Float:150"]

def get_result(filters):
	data = []
	conditions = get_conditions(filters)
	data = frappe.db.sql("""select customer_name, date, form_id, output_rate, output_sales_value, output_gst_collected, 
		output_gross from `tabGST Details` where gst_type = '-GST Output' %s """ % conditions, as_list=1)
	
	return data

def get_conditions(filters):
	conditions = ""
	if filters.get("from_date"): conditions += " and date between '%s'" %filters["from_date"]
	if filters.get("to_date"): conditions += " and '%s'" %filters["to_date"]
	
	return conditions
