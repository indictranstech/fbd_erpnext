# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import msgprint, _

class GSTDetails(Document):
	pass

#------ Add GST record on submit of Sales Invoice ----------
def set_gst_details(doc,method):
	output_rate = output_gst_collected = 0.0
	if doc.taxes:
		for tax in doc.get("taxes"):
			tax_desc = frappe.db.get_value("GST Tax Code", tax.tax_code, "description")
			output_rate = tax.rate
			output_gst_collected = tax.base_tax_amount
			tax_code = tax.tax_code

			create_gst_record(doc,method,output_rate,output_gst_collected,tax_code,tax_desc)
				
def create_gst_record(doc,method,output_rate,output_gst_collected,tax_code,tax_desc):
	tax_code_details = frappe.db.get_value("GST Tax Code", {"name":tax_code}, ["description"],as_dict=True)
	d = frappe.new_doc("GST Details")
	d.gst_type = '-GST Output'
	d.form_id = doc.name
	d.cs_name = doc.customer
	d.customer_name = doc.customer
	d.cs_gst_type = tax_desc
	d.gst_type_abbreviation = tax_code
	d.date = doc.posting_date
	d.rate = output_rate
	d.output_rate = output_rate
	d.output_sales_value = doc.total
	d.output_gst_collected = output_gst_collected
	d.save(ignore_permissions=True)

#------ Add GST record on submit of Purchase Invoice ----------
def set_gst_details_of_pi(doc,method):
	input_rate = input_gst_paid = 0.0
	if doc.taxes:
		for tax in doc.get("taxes"):
			tax_desc = frappe.db.get_value("GST Tax Code", tax.tax_code, "description")
			input_rate = tax.rate
			input_gst_paid = tax.base_tax_amount
			tax_code = tax.tax_code

			create_gst_record_of_pi(doc,method,input_rate,input_gst_paid,tax_code,tax_desc)
		
def create_gst_record_of_pi(doc,method,input_rate,input_gst_paid,tax_code,tax_desc):
	d = frappe.new_doc("GST Details")
	d.gst_type = '-GST Input'
	d.form_id = doc.name
	d.cs_name = doc.supplier
	d.supplier_name = doc.supplier
	d.cs_gst_type = tax_desc
	d.gst_type_abbreviation = tax_code
	d.date = doc.posting_date
	d.rate = input_rate
	d.input_rate = input_rate
	d.input_purchase_value = doc.total
	d.input_gst_paid = input_gst_paid
	d.save(ignore_permissions=True)

#------ Delete GST record on cancel of SI & PI -----
def del_cst_details_record(doc,method):
	if doc.doctype == 'Sales Invoice':
		gst = frappe.db.get_all("GST Details", "name", filters={"form_id": doc.name})
	elif doc.doctype == 'Purchase Invoice':
		gst = frappe.db.get_all("GST Details", "name", filters={"form_id": doc.name})
	if gst:
		for r in gst:
			frappe.delete_doc("GST Details", r['name'])


def validate_cust_gst_type(doc,method):
	# pass
	if frappe.db.get_value("Global Defaults", None, "default_company") and not doc.customer_gst_type:
		frappe.throw(_("Please select Customer GST Type First..!"))

def validate_supp_gst_type(doc,method):
	# pass
	if frappe.db.get_value("Global Defaults", None, "default_company") and not doc.supplier_gst_type:
		frappe.throw(_("Please select Supplier GST Type First..!"))