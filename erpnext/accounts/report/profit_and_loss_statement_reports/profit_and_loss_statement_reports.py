# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from erpnext.accounts.report.pl_financial_statements import \
	(get_period_list, get_columns, get_data,get_gross_profit,get_operating_profit,get_total_other_income)

def execute(filters=None):
	frappe.errprint("in execute")
	period_list = get_period_list(filters.fiscal_year, filters.periodicity)
	form_filter = filters.periodicity
	income = get_data(filters.company, "Income", "Income", "Credit", period_list,form_filter, ignore_closing_entries=True)
	cos = get_data(filters.company, "Expense", "Cost of Sales", "Debit", period_list,form_filter, ignore_closing_entries=True)
	expense = get_data(filters.company, "Expense", "Expense", "Debit", period_list,form_filter, ignore_closing_entries=True)
	other_income = get_data(filters.company, "Income", "Other Income", "Credit", period_list,form_filter, ignore_closing_entries=True)
	other_expense = get_data(filters.company, "Expense", "Other Expense", "Debit", period_list,form_filter, ignore_closing_entries=True)
	net_profit_loss = get_net_profit_loss(income, cos, expense, other_income, other_expense, period_list)

	gross_profit = get_gross_profit(income,cos,period_list)
	operating_profit = get_operating_profit(income,cos,expense,period_list)
	total_other_income = get_total_other_income(income,cos,expense,other_income,period_list)

	data = []
	data.extend(income or [])
	data.extend(cos or [])
	data.extend(gross_profit or [])
	data.extend(expense or [])
	data.extend(operating_profit or [])
	data.extend(other_income or [])
	data.extend(total_other_income or [])
	data.extend(other_expense or [])
	
	if net_profit_loss:
		data.append(net_profit_loss)

	columns = get_columns(period_list)

	return columns, data

def get_net_profit_loss(income, cos, expense, other_income, other_expense, period_list):
	if income and expense and cos and other_income and other_expense:
		net_profit_loss = {
			"account_name": "'" + _("Net Profit / Loss") + "'",
			"account": None,
			"warn_if_negative": True
		}

		for period in period_list:
			net_profit_loss[period.key] = flt((income[-2][period.key] + other_income[-2][period.key]) - \
				(expense[-2][period.key] + cos[-2][period.key] + other_expense[-2][period.key]), 3)
			
		return net_profit_loss
