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
	return [ _("ID") + ":Data:200", _("Supplier/Customer Name") + ":Data:180", _("Date") + ":Date:100",  
		_("Rate") + ":Float:100", _("Sales Value") + ":Float:120", _("Purchse Value") + ":Float:120", 
		_("GST Collected") + ":Float:120",_("GST Paid") + ":Float:120"]

def get_result(filters):
	data = []
	cond = ""
	conditions = get_conditions(filters)

	# Fetch data as per Cust/Supp GST types
	for d in frappe.get_all("GST Tax Code",fields=["name","description"],order_by="name"):
		data_list = []
		head = '"' + d['name'] + '"'
		desc = '"' + d['description'] + '"'
		
		# Fetch data as per Tax code
		rows = frappe.db.sql("""select COALESCE(form_id,CONCAT('<b>','Total','</b>')) as form_id,
			(case when form_id then null else null end) as cs_name,
			(case when form_id then null else null end) as date, 
			(case when form_id then null else null end) as rate, 
			(case when form_id then null else null end) as sales_value, 
			(case when form_id then null else null end) as purchase_value, 
			ifnull(sum(output_gst_collected),0) as get_collected, 
			ifnull(sum(input_gst_paid),0) as gst_paid from `tabGST Details` where cs_gst_type = %s %s 
			group by form_id with rollup"""%(desc,conditions), as_list=1)

		# Fetch GST Tax code details of per SI or PI
		for row in rows:
			details1 = frappe.db.sql("""select cs_name, date, rate, gst_type from `tabGST Details` where 
				form_id = '%s' and cs_gst_type = '%s' """%(row[0],d['description']), as_list=1)
			if details1:
				if details1[0][3] == "-GST Input":
					purchase_value = frappe.db.get_value("Purchase Invoice", row[0], ['total'])
					row[4] = 0.0
					row[5] = purchase_value
				else:
					sales_value = frappe.db.get_value("Sales Invoice", row[0], ['total'])
					row[4] = sales_value
					row[5] = 0.0
				
				row[1] = details1[0][0]
				row[2] = details1[0][1]
				row[3] = details1[0][2]

			data_list.append(row)

		# Create dataset as per Cust/Supp GST types
		if data_list:
			data.append(['<b>'+d['description']+'</b>','<b>'+d['name']+'</b>','','','','','',''])
			for l in data_list:
				data.append(l)
			data.append([])

	if filters.get("from_date"): cond += "where date between '%s'" %filters["from_date"]
	if filters.get("to_date"): cond += " and '%s'" %filters["to_date"]

	# Add total row for GST Paid and GST Collected
	total_value = frappe.db.sql("""select ifnull(sum(output_gst_collected),0) as gst_collected,
		ifnull(sum(input_gst_paid),0) as gst_paid from `tabGST Details` %s """ %(cond),as_list=1)

	# Calculate total of GST Collected and Paid
	if data:
		data.append(['<b>'+'Grand Total'+'</b>','','','','','',total_value[0][0],total_value[0][1]])

	return data 

# Add Date Filters on dataset
def get_conditions(filters):
	conditions = ""
	if filters.get("from_date"): conditions += " and date between '%s'" %filters["from_date"]
	if filters.get("to_date"): conditions += " and '%s'" %filters["to_date"]

	return conditions
