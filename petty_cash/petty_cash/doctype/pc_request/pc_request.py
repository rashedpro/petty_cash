# Copyright (c) 2023, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from erpnext.accounts.doctype.payment_entry.payment_entry import get_party_details
from frappe.utils import flt
from frappe.utils import get_link_to_form


class PCRequest(Document):
	def validate(self):
		self.validate_repeating_expense_type()
		self.sum_total_advance_amount()
		self.set_petty_cash_account()
		self.calculate_percentage_of_total()
		self.validate_allowed_expense_of_total_amount()
		self.set_previous_balance()

	def validate_repeating_expense_type(self):
		"""Error when Same Company is entered multiple times in accounts"""
		expense_list = []
		for expense in self.expense_details:
			expense_list.append(expense.expense_type)

		if len(expense_list) != len(set(expense_list)):
			frappe.throw(_("Same Expense Type is entered more than once"))

	def sum_total_advance_amount(self):
		self.total_amount=0
		for expense in self.expense_details:
			self.total_amount=self.total_amount+expense.advance_amount

	def set_petty_cash_account(self):
		self.petty_cash_account=fetch_petty_cash_account(self.company)
		if self.petty_cash_account==None:
			frappe.throw(_("Petty cash account is not defined for {0}. Please check {1}".format(self.company,get_link_to_form("PC Settings", "PC Settings"))))

	def set_previous_balance(self):
		self.previous_balance=flt(get_balance_of_account_for_an_employee(company=self.company,account=self.petty_cash_account,party=self.employee,to_date=self.date))


	def calculate_percentage_of_total(self):
		for expense_item in self.expense_details:
			expense_item.actual_percentage_of_total_for_amt_advance_amount=flt((expense_item.advance_amount/self.total_amount)*100,2)

	def validate_allowed_expense_of_total_amount(self):
		for expense_item in self.expense_details:
			expense_type_to_check=expense_item.expense_type
			allowed_percent_of_total_request=frappe.db.get_value('PC Expense Type', expense_type_to_check, 'allowed_percent_of_total_request')
			max_allowed_request_amount=frappe.db.get_value('PC Expense Type', expense_type_to_check, 'max_allowed_request_amount')
			if max_allowed_request_amount>0 and expense_item.advance_amount>max_allowed_request_amount:
					frappe.throw(_("For expense type {0}, Max. Allowed Request Amount is {1} whereas actual is {2}."
					.format(expense_item.expense_type,frappe.bold(max_allowed_request_amount),frappe.bold(expense_item.advance_amount))))						
			if allowed_percent_of_total_request>0:
				expense_type_to_check_actual_per=flt((expense_item.advance_amount/self.total_amount)*100,2)
				if expense_type_to_check_actual_per>allowed_percent_of_total_request:
					frappe.throw(_("For expense type {0}, allowed percentage of total request is {1} % whereas actual is {2} %."
					.format(expense_item.expense_type,frappe.bold(allowed_percent_of_total_request),frappe.bold(expense_type_to_check_actual_per))))		



@frappe.whitelist()
def fetch_petty_cash_account(company):
	petty_cash_account=frappe.db.get_all('PC Petty Cash Account Detail',filters={'company': company},fields=['petty_cash_account'])
	if len(petty_cash_account)>0:
		petty_cash_account=petty_cash_account[0].get('petty_cash_account')
	else:
		petty_cash_account=None		
	return petty_cash_account

#  called from PE hook
@frappe.whitelist()
def update_pc_request_fields(self,method):
	if self.custom_pc_request_reference:
		print('--'*10,self.docstatus)
		pe_list = frappe.db.sql("""		
		select sum(paid_amount) as total_paid_amount from `tabPayment Entry` where docstatus=1 and custom_pc_request_reference=%(custom_pc_request_reference)s""",
		{"custom_pc_request_reference": self.custom_pc_request_reference},as_dict=True,	)
		print(pe_list,'pe_list')
		if pe_list and len(pe_list)>0 and pe_list[0].total_paid_amount:	
			frappe.db.set_value('PC Request',self.custom_pc_request_reference , 'actual_paid_amount', pe_list[0].total_paid_amount)
			actual_paid_amount = frappe.db.get_value('PC Request',self.custom_pc_request_reference, 'actual_paid_amount')
			total_amount = frappe.db.get_value('PC Request',self.custom_pc_request_reference, 'total_amount')
			payment_status=None
			if total_amount>actual_paid_amount:
				payment_status='Partially Paid'
				frappe.db.set_value('PC Request',self.custom_pc_request_reference , 'payment_status',payment_status )
			elif total_amount==actual_paid_amount:	
				payment_status= 'Fully Paid'
				frappe.db.set_value('PC Request',self.custom_pc_request_reference , 'payment_status',payment_status)
			elif actual_paid_amount==0:
				payment_status='Not Paid'
				frappe.db.set_value('PC Request',self.custom_pc_request_reference , 'payment_status',payment_status )
			elif actual_paid_amount>total_amount:
				frappe.throw(_("{0} has requested total amount as {1} and total actual paid amount will become {2} <br> Total paid amount should not exceed requested amount."
				   .format(get_link_to_form('PC Request',self.custom_pc_request_reference),frappe.bold(total_amount),frappe.bold(actual_paid_amount))))

			frappe.msgprint(
					_("PC Request {0} is updated with acutal paid amount {1} and payment status {2}"
	   				.format(self.custom_pc_request_reference,actual_paid_amount,payment_status)), alert=True, indicator="green")	
		else:
			# a single PE is cancelled
			actual_paid_amount=0
			frappe.db.set_value('PC Request',self.custom_pc_request_reference , 'actual_paid_amount',actual_paid_amount)
			payment_status='Not Paid'
			frappe.db.set_value('PC Request',self.custom_pc_request_reference , 'payment_status', payment_status)
			frappe.msgprint(
					_("PC Request {0} is updated with acutal paid amount {1} and payment status {2}"
	   				.format(self.custom_pc_request_reference,actual_paid_amount,payment_status)), alert=True, indicator="green")

			 
@frappe.whitelist()		
def get_balance_of_account_for_an_employee(company,account,party,to_date,party_type='Employee'):
	account_filter = ""
	if account:
		account_filter = "and account = %s" % (frappe.db.escape(account))
	gle = frappe.db.sql(
		"""
		select party, sum(debit) as debit, sum(credit) as credit, (sum(debit)-sum(credit))as balance
		from `tabGL Entry`
		where company=%(company)s
			and is_cancelled = 0
			and ifnull(party_type, '') = %(party_type)s 
			and ifnull(party, '') =  %(party)s

			and posting_date <= %(to_date)s
			and ifnull(is_opening, 'No') = 'No'
			{account_filter}
		group by party""".format(
			account_filter=account_filter
		),
		{
			"company": company,
			"party_type": party_type,
			"party":party,
			"to_date": to_date,
		},
		as_dict=True,
	)
	# balances_within_period = frappe._dict()
	# for d in gle:
	# 	balances_within_period.setdefault(d.party, [d.debit, d.credit])
	if gle and len(gle)>0:
		return gle[0].balance
	else:
		return 0