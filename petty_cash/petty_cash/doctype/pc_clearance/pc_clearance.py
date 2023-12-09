# Copyright (c) 2023, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from erpnext.controllers.accounts_controller import get_default_taxes_and_charges
from frappe.utils import flt,nowdate,cint

class PCClearance(Document):
	def validate(self):
		self.synch_clearance_details_and_stock_item_details()
		self.calculate_amount_for_stock_expense_type()
		self.calculate_amount_with_tax()
		self.calculate_total_amount()
		self.validate_allowed_expense_of_total_amount()
	
	def validate_no_stock_item_present_for_material(self):
		# raise if no item for material
		#  total in clearance
		for clearance_item in self.clearance_details:
			if clearance_item.is_non_stock_expense_type==0:
				clearance_detail_row_idx=clearance_item.idx
				stock_item_found=False
				for stock_item in self.stock_item_details:
					if cint(stock_item.clearance_detail_row_idx)==cint(clearance_detail_row_idx):
						stock_item_found=True
						break
				if stock_item_found==False:
					frappe.throw(_("No stock item defined for expense {0} : Row id {1}".format(clearance_item.expense_type,clearance_item.idx)))

	def on_submit(self):
		default_petty_cash_account=self.get_default_petty_cash_account
		# self.create_je_for_non_taxable_and_non_stock_items(default_petty_cash_account)
		self.create_pi_for_taxable_items()
		# self.clearance_journal_entry=self.create_consolidated_clearance_journal_entry(default_petty_cash_account)

	def validate_allowed_expense_of_total_amount(self):
		for clearance_item in self.clearance_details:
			expense_type_to_check=clearance_item.expense_type
			expense_type_to_check_total_amount=0
			allowed_percent_of_total_clearance=frappe.db.get_value('PC Expense Type', expense_type_to_check, 'allowed_percent_of_total_clearance')
			max_allowed_amt_wo_tax=frappe.db.get_value('PC Expense Type', expense_type_to_check, 'max_allowed_amt_wo_tax')
			if allowed_percent_of_total_clearance>0:
				for clearance_item_to_check in self.clearance_details:
					if expense_type_to_check==clearance_item_to_check.expense_type:
						expense_type_to_check_total_amount=expense_type_to_check_total_amount+clearance_item_to_check.amount
				if max_allowed_amt_wo_tax>0 and expense_type_to_check_total_amount>max_allowed_amt_wo_tax:
					frappe.throw(_("For expense type {0}, Max. Allowed Amount Without Tax is {1} whereas actual is {2}.".format
					(clearance_item.expense_type,frappe.bold(max_allowed_amt_wo_tax),frappe.bold(expense_type_to_check_total_amount))))						
				expense_type_to_check_actual_per=flt((expense_type_to_check_total_amount/self.total_expense_without_tax)*100,2)
				if expense_type_to_check_actual_per>allowed_percent_of_total_clearance:
					frappe.throw(_("For expense type {0}, allowed percentage of total without tax is {1} % whereas actual is {2} %.".format
					(clearance_item.expense_type,frappe.bold(allowed_percent_of_total_clearance),frappe.bold(expense_type_to_check_actual_per))))		



	def synch_clearance_details_and_stock_item_details(self):	
		#  check if is_non_stock_expense_type==1 , then remove
		for clearance_item in self.clearance_details:
			if clearance_item.is_non_stock_expense_type==1:
				clearance_detail_row_idx=clearance_item.idx
				for stock_item in self.stock_item_details:
					if cint(stock_item.clearance_detail_row_idx)==cint(clearance_detail_row_idx):
						self.remove(stock_item)

	def calculate_amount_for_stock_expense_type(self):
		#  total in clearance
		for clearance_item in self.clearance_details:
			if clearance_item.is_non_stock_expense_type==0:
				clearance_detail_row_idx=clearance_item.idx
				total_amount=0
				for stock_item in self.stock_item_details:
					if cint(stock_item.clearance_detail_row_idx)==cint(clearance_detail_row_idx):
						amount=stock_item.qty*stock_item.rate
						stock_item.total=amount
						total_amount=total_amount+amount
				clearance_item.amount=total_amount


	def calculate_amount_with_tax(self):
		for clearance_item in self.clearance_details:
			if clearance_item.is_tax_applicable==1:
				taxes = get_default_taxes_and_charges("Purchase Taxes and Charges Template",company=self.company)
				print('taxes',taxes,clearance_item.idx,'--'*10)
				if taxes.get("taxes"):
					amount_with_tax=clearance_item.amount+ (clearance_item.amount*taxes.get("taxes")[0].rate)/100
					clearance_item.amount_with_tax=amount_with_tax
					print(clearance_item.amount_with_tax,'clearance_item.amount_with_tax')
			else:
				clearance_item.amount_with_tax=clearance_item.amount


	def calculate_total_amount(self):
		total_expense=0
		total_petty_cash=0
		remaining_amount=0
		total_expense_without_tax=0
		if len(self.clearance_details)>0:
			for clearance_item in self.clearance_details:
				total_expense=total_expense+ (clearance_item.amount_with_tax or 0)
				total_expense_without_tax=total_expense_without_tax+ (clearance_item.amount or 0)
		self.total_expense_without_tax=total_expense_without_tax
		self.total_expense=total_expense
		self.total_petty_cash=self.previous_balance or 0
		self.remaining_amount=self.total_expense-self.total_petty_cash

	def get_default_petty_cash_account(self):
		petty_cash_account_list=frappe.db.get_list('PC Petty Cash Account Detail', filters={'company': self.company},fields=['petty_cash_account'])		
		if len(petty_cash_account_list)>0:
			default_petty_cash_account=petty_cash_account_list[0].get('petty_cash_account')
			return default_petty_cash_account
		else:
			frappe.throw(_("Petty Cash Account is not defined for {0} company".format(self.company)))


	def get_default_zero_tax_template(self):
		zero_tax_template_list=frappe.db.get_list('PC Purchase Taxes Template Detail', filters={'company': self.company},fields=['zero_tax_template'])		
		if len(zero_tax_template_list)>0:
			default_zero_tax_template=zero_tax_template_list[0].get('zero_tax_template')
			return default_zero_tax_template
		else:
			frappe.throw(_("Zero Tax Template is not defined for {0} company".format(self.company)))

	def get_default_expense_account(self,expense_type,company):
		expense_type_doc = frappe.get_doc('PC Expense Type',expense_type)
		default_expense_account=None
		# default_non_stock_item=expense_type.default_non_stock_item
		for account in expense_type_doc.accounts:
			if account.company==company:
				default_expense_account=account.default_account
				break
		if default_expense_account:
			return default_expense_account
		else:
			frappe.throw(_("Expense Account is not defined for {0} company".format(company)))



	def create_pi_for_taxable_items(self):
		for clearance_item in self.clearance_details:
			if clearance_item.is_tax_applicable==1 or (clearance_item.is_tax_applicable==0 and clearance_item.is_non_stock_expense_type==0):
				supplier=clearance_item.supplier
				bill_no=clearance_item.bill_no
				project=clearance_item.project
				cost_center=clearance_item.cost_center
				clearance_detail_row_idx=clearance_item.idx
				is_non_stock_expense_type=clearance_item.is_non_stock_expense_type
				expense_type=clearance_item.expense_type
				is_tax_applicable=clearance_item.is_tax_applicable
				expense_date=clearance_item.expense_date
				clearance_item.pi_jv_reference=self.create_purchase_invoice(supplier,bill_no,project,cost_center,clearance_detail_row_idx,is_non_stock_expense_type,expense_type,is_tax_applicable,expense_date)


	def create_purchase_invoice(self,supplier,bill_no,project,cost_center,clearance_detail_row_idx,is_non_stock_expense_type,expense_type,is_tax_applicable,expense_date):
		pi=frappe.new_doc('Purchase Invoice')
		print('clearance_detail_row_idx',clearance_detail_row_idx)
		pi.posting_date=expense_date
		pi.supplier=supplier
		pi.company=self.company
		pi.bill_no=bill_no
		pi.project=project
		if is_non_stock_expense_type==0:
			print('111111')
			pi.update_stock=1
			for stock_item in self.stock_item_details:
				print('stock_item',stock_item,stock_item.clearance_detail_row_idx,clearance_detail_row_idx,stock_item.clearance_detail_row_idx==clearance_detail_row_idx,type(stock_item.clearance_detail_row_idx),type(clearance_detail_row_idx))
				if cint(stock_item.clearance_detail_row_idx)==cint(clearance_detail_row_idx):
					print('22in')		
					pi_item=pi.append('items',{})
					pi_item.item_code=stock_item.item_code
					pi_item.qty=stock_item.qty
					pi_item.rate=stock_item.rate
					# pi_item.expense_account=default of PI as material
					pi_item.cost_center=cost_center
					pi_item.project=project
					pi_item.warehouse=stock_item.warehouse
		elif is_non_stock_expense_type==1:
			pi.update_stock=0
			pi_item=pi.append('items',{})
			pi_item.item_code=frappe.db.get_value('PC Expense Type',expense_type, 'default_non_stock_item')
			pi_item.expense_account=self.get_default_expense_account(expense_type,self.company)
			pi_item.qty=1
			pi_item.cost_center=cost_center
			pi_item.project=project			
		if is_non_stock_expense_type==0 and is_tax_applicable==1:
			taxes = get_default_taxes_and_charges("Purchase Taxes and Charges Template",company=self.company)
			if taxes.get("taxes_and_charges"):
				pi.taxes_and_charges=taxes.get("taxes_and_charges")
		elif is_non_stock_expense_type==0 and is_tax_applicable==0:
			pi.taxes_and_charges=self.get_default_zero_tax_template()
		pi.custom_pc_clearance_reference=self.name
		pi.run_method("set_missing_values")
		pi.run_method("calculate_taxes_and_totals")		
		print(pi.as_dict())
		pi.save(ignore_permissions = True)				
		pi.submit()	
		return pi.name					

	def create_je_for_non_taxable_and_non_stock_items(self,default_petty_cash_account):
		for clearance_item in self.clearance_details:
			# Only case, we doNOT create PI is when  is_non_stock_expense_type=1 and is_tax_applicable=0
			if clearance_item.is_non_stock_expense_type==1 and clearance_item.is_tax_applicable==0:
				# expense_type = frappe.get_doc('PC Expense Type', clearance_item.expense_type)
				# # default_non_stock_item=expense_type.default_non_stock_item
				# for account in expense_type.accounts:
				# 	if account.company==self.company:
				# 		default_expense_account=account.default_account
				# 		break
				expense_type=clearance_item.expense_type
				clearance_detail_row_idx=clearance_item.idx
				debit_account=self.get_default_expense_account(expense_type,self.company)
				credit_account=default_petty_cash_account
				expense_amount=clearance_item.amount_with_tax	
				bill_no=clearance_item.bill_no
				cost_center=clearance_item.cost_center
				journal_entry=self.create_journal_entry(expense_type,clearance_detail_row_idx,debit_account,credit_account,expense_amount,bill_no,cost_center)
				clearance_item.pi_jv_reference=journal_entry


	def create_journal_entry(self,expense_type,clearance_detail_row_idx,debit_account,credit_account,expense_amount,bill_no,cost_center):
		accounts = []
		# debit entry
		accounts.append({
			"account": debit_account,
			"debit_in_account_currency": expense_amount,
			"cost_center": cost_center
		})
		# credit entry
		accounts.append({
			"account": credit_account,
			"credit_in_account_currency": expense_amount,
			"cost_center":  cost_center,
			"party_type":"Employee",
			"party":self.employee
		})
		
		user_remark="It is auto created on submit of PC Clearance {0}, Expense Type {1}, Row # {2}".format
		(self.name,expense_type,clearance_detail_row_idx)
		
		journal_entry = frappe.new_doc('Journal Entry')
		journal_entry.voucher_type = 'Journal Entry'
		journal_entry.company = self.company
		journal_entry.user_remark =user_remark
		journal_entry.bill_no=bill_no
		journal_entry.posting_date =self.clearance_date
		journal_entry.set("accounts", accounts)
		journal_entry.custom_pc_clearance_reference=self.name
		journal_entry.save(ignore_permissions = True)				
		journal_entry.submit()	
		return journal_entry.name
		# msg = _('Journal Entry {0} is created.'.format(frappe.bold(get_link_to_form('Journal Entry',journal_entry.name))))   
		# frappe.msgprint(msg)	


	def create_consolidated_clearance_journal_entry(self,default_petty_cash_account):
		default_payable_account = frappe.db.get_value('Company', self.company, 'default_payable_account')
		default_cost_center=frappe.db.get_value('Company', self.company, 'cost_center')
		if not default_payable_account:
			frappe.throw(_("Default Payable Account is not defined for {0} company".format(self.company)))
		debit_account=default_payable_account
		credit_account=default_petty_cash_account
		accounts = []
		clearance_detail_row_idx=[]
		for clearance_item in self.clearance_details:
			if clearance_item.is_tax_applicable==1 or (clearance_item.is_tax_applicable==0 and clearance_item.is_non_stock_expense_type==0):
				clearance_detail_row_idx.append(clearance_item.idx)
				# debit entry
				accounts.append({
					"account": debit_account,
					"debit_in_account_currency": clearance_item.amount_with_tax,
					"cost_center": default_cost_center or '',
					"party_type":"Supplier",
					"party":clearance_item.supplier,				
				})
				# credit entry
				accounts.append({
					"account": credit_account,
					"credit_in_account_currency": clearance_item.amount_with_tax,
					"cost_center": default_cost_center or '',
					"party_type":"Employee",
					"party":self.employee,
					"reference_type":"Purchase Invoice",
					"reference_name":clearance_item.pi_jv_reference
				})
		
		if len(accounts)>0:
			user_remark="It is a consolidated JE auto created on submit of PC Clearance {0}, Row # {1}".format
			(self.name,",".join(clearance_detail_row_idx))
			
			journal_entry = frappe.new_doc('Journal Entry')
			journal_entry.voucher_type = 'Journal Entry'
			journal_entry.company = self.company
			journal_entry.user_remark =user_remark
			# todo : journal_entry.bill_no=bill_no
			journal_entry.posting_date = self.clearance_date
			journal_entry.set("accounts", accounts)
			journal_entry.custom_pc_clearance_reference=self.name
			journal_entry.save(ignore_permissions = True)				
			journal_entry.submit()	
			return journal_entry.name
		else:
			return None
		
		# msg = _('Journal Entry {0} is created.'.format(frappe.bold(get_link_to_form('Journal Entry',journal_entry.name))))   
		# frappe.msgprint(msg)	