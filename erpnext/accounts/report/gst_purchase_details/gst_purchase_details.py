# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, getdate, cstr
from frappe import _
from datetime import date, timedelta

def execute(filters=None):
	columns, out = [], []
	validate_filters(filters)
	columns = get_columns()
	out = get_result(filters)

	return columns, out

def validate_filters(filters):
	if filters.from_date > filters.to_date:
		frappe.throw(_("To Date must be greater than From Date"))

def get_columns():
	return [_("Supplier Name") + ":Link/Supplier:160", _("ID") + ":Link/Purchase Invoice:200", _("Date") + ":Date:120",  
		_("Rate") + ":Float:120", _("Purchase Value") + ":Float:120", _("GST Paid") + ":Float:150",
		_("Gross") + ":Float:150"]

def get_result(filters):
	data = []
	conditions = get_conditions(filters)
	with_gst = frappe.db.sql("""select supplier_name, form_id, date, sum(input_rate), sum(input_purchase_value), 
		sum(input_gst_paid), sum(input_gross) from `tabGST Details` where supplier_gst_type = 'Purchase with GST' and 
		gst_type = '-GST Input' %s group by form_id with rollup""" % conditions, as_list=1)
			
	exepted_gst = frappe.db.sql("""select supplier_name, form_id, date, sum(input_rate), sum(input_purchase_value), 
		sum(input_gst_paid), sum(input_gross) from `tabGST Details` where supplier_gst_type = 'Purchases exempted from GST' 
		and gst_type = '-GST Input' %s group by form_id with rollup""" % conditions, as_list=1)

	non_taxable = frappe.db.sql("""select supplier_name, form_id, date, sum(input_rate), sum(input_purchase_value), 
		sum(input_gst_paid), sum(input_gross) from `tabGST Details` where supplier_gst_type = 'Non-Taxable' and 
		gst_type = '-GST Input' %s group by form_id with rollup""" % conditions, as_list=1)
	
	non_gst_reg = frappe.db.sql("""select supplier_name, form_id, date, sum(input_rate), sum(input_purchase_value), 
		sum(input_gst_paid), sum(input_gross) from `tabGST Details` where supplier_gst_type = 'Non GST-registered Supplier' 
		and gst_type = '-GST Input' %s group by form_id with rollup""" % conditions, as_list=1)


	heading = """<b>GST Report Items</b>,<b>Purchases with GST</b>,<b>Grand Total</b>,<b>Non-GST Report Items</b>,
		<b>Purchases exempted from GST</b>,<b>Non-Taxable</b>,<b>Non GST-registered Supplier</b>"""

	heading_val = """<b>GST Purchase Details</b>"""
	
	add_total_rows(data, with_gst, exepted_gst, non_taxable, non_gst_reg, heading)

	return data 

def add_total_rows(data, with_gst, exepted_gst, non_taxable, non_gst_reg, heading):
	data.append([heading[0:23],'','','','','',''])
	data.append(['TX7',heading[24:49],'','','','',''])
	if with_gst:
		for d in with_gst:
			data.append(d)
		data.append([])
		data.append(['',heading[50:68],'','',with_gst[-1][4],with_gst[-1][5],with_gst[-1][6]])
		data.append([])
	data.append([])

	data.append([heading[69:96],'','','','','',''])
	data.append(['EP',heading[97:130],'','','','',''])
	if exepted_gst:
		for d in exepted_gst:
			data.append(d)
	data.append([])

	data.append(['N-T',heading[135:149],'','','','',''])
	if non_taxable:
		for d in non_taxable:
			data.append(d)
	data.append([])

	data.append(['NR',heading[154:184],'','','','',''])
	if non_gst_reg:
		for d in non_gst_reg:
			data.append(d)

	return data

def get_conditions(filters):
	conditions = ""
	if filters.get("from_date"): conditions += " and date between '%s'" %filters["from_date"]
	if filters.get("to_date"): conditions += " and '%s'" %filters["to_date"]

	return conditions
 