from __future__ import unicode_literals
import frappe
from frappe import _, _dict
from frappe.utils import (flt, getdate, get_first_day, get_last_day,
	add_months, add_days, formatdate)

def get_period_list(fiscal_year, periodicity, from_beginning=False):
	"""Get a list of dict {"to_date": to_date, "key": key, "label": label}
		Periodicity can be (Yearly, Quarterly, Monthly)"""

	fy_start_end_date = frappe.db.get_value("Fiscal Year", fiscal_year, ["year_start_date", "year_end_date"])
	if not fy_start_end_date:
		frappe.throw(_("Fiscal Year {0} not found.").format(fiscal_year))

	start_date = getdate(fy_start_end_date[0])
	# frappe.errprint(["Year Start", start_date])
	end_date = getdate(fy_start_end_date[1])
	# frappe.errprint(["Year Start", end_date])

	# frappe.errprint(["year==",fiscal_year])
	# frappe.errprint(["Period=", periodicity])	

	if periodicity == "Yearly":
		period_list = [_dict({"to_date": end_date, "key": fiscal_year, "label": fiscal_year})]
	else:
		months_to_add = {
			# "Half-yearly": 6,
			# "Quarterly": 3,
			"Monthly": 1
		}[periodicity]

		period_list = []

		# start with first day, so as to avoid year to_dates like 2-April if ever they occur
		to_date = get_first_day(start_date)
		
		for i in xrange(12 / months_to_add):
			to_date = add_months(to_date, months_to_add)
			if to_date == get_first_day(to_date):
				# if to_date is the first day, get the last day of previous month
				to_date = add_days(to_date, -1)
			else:
				# to_date should be the last day of the new to_date's month
				to_date = get_last_day(to_date)

			if to_date <= end_date:
				# the normal case
				period_list.append(_dict({ "to_date": to_date }))

				# if it ends before a full year
				if to_date == end_date:
					break

			else:
				# if a fiscal year ends before a 12 month period
				period_list.append(_dict({ "to_date": end_date }))
				break

	# common processing
	for opts in period_list:
		key = opts["to_date"].strftime("%b_%Y").lower()
		label = formatdate(opts["to_date"], "MMM YYYY")
		opts.update({
			"key": key.replace(" ", "_").replace("-", "_"),
			"label": label,
			"year_start_date": start_date,
			"year_end_date": end_date
		})

		if from_beginning:
			# set start date as None for all fiscal periods, used in case of Balance Sheet
			opts["from_date"] = None
		else:
			opts["from_date"] = start_date

	return period_list

def get_data(company, root_type, account_subtype, balance_must_be, period_list,form_filter, ignore_closing_entries=False):
	accounts = get_accounts(company, root_type, account_subtype)
	if not accounts:
		return None

	accounts_by_name = filter_accounts(accounts)
	gl_entry=[]
	for acc in accounts:
		if form_filter== 'Yearly':
			gl_entries_by_account = get_gl_entries(company, period_list[0]["from_date"], period_list[0]["to_date"],
			acc.lft, acc.rgt, acc.account_subtype, gl_entry,form_filter, ignore_closing_entries=ignore_closing_entries)
		else:
			for period in period_list:
				gl_entries_by_account = get_gl_entries(company, period["from_date"], period["to_date"],
					acc.lft, acc.rgt, acc.account_subtype, gl_entry, form_filter, ignore_closing_entries=ignore_closing_entries)
	calculate_values(account_subtype,accounts_by_name,gl_entry, period_list,form_filter)
	out = prepare_data(accounts, balance_must_be, period_list)

	if out:
		add_total_row(out, account_subtype, period_list)
	return out

	# if period_list:

def calculate_values(account_subtype,accounts_by_name, gl_entry, period_list,form_filter):
	if form_filter == 'Yearly':
		for entries in gl_entry:
			if entries:
				d = accounts_by_name.get(entries[0]['account'])
			for entry in entries:
				for period in period_list:
					if entry.posting_date <= period.to_date:
						d[period.key] = d.get(period.key, 0.0) + flt(entry.debit) - flt(entry.credit)
	else:
		for entries in gl_entry:
			if entries:
				d = accounts_by_name.get(entries[0]['account'])
			for entry in entries:
				for period in period_list:
					if entry.posting_date.month == period.to_date.month:
						if entry.posting_date <= period.to_date :
							d[period.key] = d.get(period.key, 0.0) + flt(entry.debit) - flt(entry.credit)

def filter_accounts(accounts, depth=10):
	parent_children_map = {}
	accounts_by_name = {}
	for d in accounts:
		accounts_by_name[d.name] = d
		parent_children_map.setdefault(d.account_subtype or None, []).append(d)

	return accounts_by_name

def prepare_data(accounts, balance_must_be, period_list):
	out = []
	year_start_date = period_list[0]["year_start_date"].strftime("%Y-%m-%d")
	year_end_date = period_list[-1]["year_end_date"].strftime("%Y-%m-%d")

	for d in accounts:
		# add to output
		has_value = False
		row = {
			"account_name": d.account_name,
			"account": d.name,
			# "parent_account": d.parent_account,
			"account_subtype":d.account_subtype,
			"indent": flt(d.indent),
			"from_date": year_start_date,
			"to_date": year_end_date
		}
		for period in period_list:
			if d.get(period.key):
				# change sign based on Debit or Credit, since calculation is done using (debit - credit)
				d[period.key] *= (1 if balance_must_be=="Debit" else -1)

			row[period.key] = flt(d.get(period.key, 0.0), 3)

			if abs(row[period.key]) >= 0.005:
				# ignore zero values
				has_value = True

		if has_value:
			out.append(row)

	return out

def add_total_row(out, account_subtype, period_list):
	row = {
		"account_name": "'" + _("Total ({0})").format(account_subtype) + "'",
		"account": None
	}
	for period in period_list:
		tot = 0.0
		for i in out:
			tot = tot + i.get(period.key, 0.0)
			row[period.key] = tot

	out.append(row)

	# blank row after Total
	out.append({})

def get_accounts(company, root_type, account_subtype):
	return frappe.db.sql("""select name, parent_account, lft, rgt, root_type, report_type, account_name,account_subtype 
		from `tabAccount` where company=%s and root_type=%s and account_subtype=%s order by lft""", 
		(company, root_type, account_subtype), as_dict=True)

def get_gl_entries(company, from_date, to_date, root_lft, root_rgt, account_subtype, gl_entry, form_filter, ignore_closing_entries=False):
	"""Returns a dict like { "account": [gl entries], ... }"""
	
	additional_conditions = []

	if ignore_closing_entries:
		additional_conditions.append("and ifnull(voucher_type, '')!='Period Closing Voucher'")

	if from_date:
		additional_conditions.append("and posting_date >= %(from_date)s")

	gl_entries = frappe.db.sql("""select posting_date, account, debit, credit, is_opening from `tabGL Entry`
		where company=%(company)s
		{additional_conditions}
		and posting_date <= %(to_date)s
		and account in (select name from `tabAccount`
			where lft >= %(lft)s and rgt <= %(rgt)s and account_subtype=%(account_subtype)s)
		order by account, posting_date""".format(additional_conditions="\n".join(additional_conditions)),
		{
			"company": company,
			"from_date": from_date,
			"to_date": to_date,
			"lft": root_lft,
			"rgt": root_rgt,
			"account_subtype":account_subtype
		},
		as_dict=True)
	
	# gl_entry.append(gl_entries)

	if form_filter == 'Yearly':
		gl_entry.append(gl_entries)
	else :
		if gl_entries:
			if gl_entries[0]['posting_date'].month == to_date.month:
				gl_entry.append(gl_entries)

	return gl_entry


def get_columns(period_list):
	columns = [{
		"fieldname": "account",
		"label": _("Account"),
		"fieldtype": "Link",
		"options": "Account",
		"width": 300
	}]
	for period in period_list:
		columns.append({
			"fieldname": period.key,
			"label": period.label,
			"fieldtype": "Currency",
			"width": 150
		})

	return columns

def get_gross_profit(income,cos,period_list):
	row = {
		"account_name": "'" + _("Gross Profit") + "'",
		"account": None
	}
	if income and cos:
		for period in period_list:
			gross_profit = income[-2][period.key] - cos[-2][period.key]
			row[period.key] = gross_profit

	cos.append(row)

	cos.append({})

def get_operating_profit(income,cos,expense,period_list):
	row = {
		"account_name": "'" + _("Operating Profit") + "'",
		"account": None
	}
	if income and cos and expense:
		for period in period_list:
			operating_profit = 500
			row[period.key] = operating_profit

	expense.append(row)

	expense.append({})

def get_total_other_income(income,cos,expense,other_income,period_list):
	row = {
		"account_name": "'" + _("Total Other Income") + "'",
		"account": None
	}
	if income and cos and expense and other_income:
		for period in period_list:
			# frappe.errprint(["GF=",income])
			# frappe.errprint(["COS=",expense[-2][period.key]])
			total_other_income = 500
			row[period.key] = total_other_income

	other_income.append(row)

	other_income.append({})
