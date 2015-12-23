# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, getdate, cstr, cint
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
	return [ _("ID") + ":Data:150", _("Supplier/Customer Name") + ":Data:180", _("Date") + ":Date:120",  
		_("Rate") + ":Float:120", _("Sales Value") + ":Float:120", _("Purchase Value") + ":Float:120", 
		_("GST Collected") + ":Float:120",_("GST Paid") + ":Float:120"]

def get_result(filters):
	data = []
	cond = ""
	conditions = get_conditions(filters)

	for d in frappe.get_all("GST Types",fields=["name","gst_type_abbreviation"],order_by="name"):
		head = '"' + d['name'] + '"'
		row = frappe.db.sql("""select COALESCE(form_id,CONCAT('<b>','Total','</b>')),(case when form_id is null then null else 
			cs_name end) as cs_name,(case when form_id is null then null else date end) as date, ifnull((case when form_id is 
			null then '' else rate end),0) as rate, ifnull(sum(output_sales_value),0), ifnull(sum(input_purchase_value),0), 
			ifnull(sum(output_gst_collected),0), ifnull(sum(input_gst_paid),0) from `tabGST Details` where cs_gst_type = %s %s 
			group by form_id with rollup""" %(head,conditions), as_list=1)
		if row:
			data.append(['<b>'+d['gst_type_abbreviation']+'</b>','<b>'+d['name']+'</b>','','','','','',''])
			for r in row:
				data.append(r)
			data.append([])


	if filters.get("from_date"): cond += "where date between '%s'" %filters["from_date"]
	if filters.get("to_date"): cond += " and '%s'" %filters["to_date"]

	total_value = frappe.db.sql("""select ifnull(sum(output_gst_collected),0) ,ifnull(sum(input_gst_paid),0) from 
		`tabGST Details` %s """ %(cond),as_list=1)
	if data:
		data.append(['<b>'+'Grand Total'+'</b>','','','','','',total_value[0][0],total_value[0][1]])

	return data 

def get_conditions(filters):
	conditions = ""
	if filters.get("from_date"): conditions += " and date between '%s'" %filters["from_date"]
	if filters.get("to_date"): conditions += " and '%s'" %filters["to_date"]

	return conditions
