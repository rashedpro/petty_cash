# Copyright (c) 2023, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class PCSettings(Document):
	def validate(self):
		self.validate_repeating_companies('default_petty_cash_accounts')
		self.validate_repeating_companies('zero_tax_template_for_purchase_expenses')
		self.validate_purchase_tax_template()
		self.validate_accounts()

	def validate_repeating_companies(self,child_table):
		"""Error when Same Company is entered multiple times in accounts"""
		accounts_list = []
		for entry in self.get(child_table):
			accounts_list.append(entry.company)

		if len(accounts_list) != len(set(accounts_list)):
			if child_table=='zero_tax_template_for_purchase_expenses':
				frappe.throw(_("Same Company is entered more than once in Zero Tax Template for Purchase Expense"))
			else:
				frappe.throw(_("Same Company is entered more than once in Default Petty Cash Account"))

	def validate_purchase_tax_template(self):
		for entry in self.zero_tax_template_for_purchase_expenses:
			"""Error when Company of Ledger account doesn't match with Company Selected"""
			if frappe.db.get_value("Purchase Taxes and Charges Template", entry.zero_tax_template, "company") != entry.company:
				frappe.throw(
					_("Template {0} does not match with Company {1}").format(entry.zero_tax_template, entry.company)
				)

	def validate_accounts(self):
		for entry in self.default_petty_cash_accounts:
			"""Error when Company of Ledger account doesn't match with Company Selected"""
			if frappe.db.get_value("Account", entry.petty_cash_account, "company") != entry.company:
				frappe.throw(
					_("Account {0} does not match with Company {1}").format(entry.petty_cash_account, entry.company)
				)				