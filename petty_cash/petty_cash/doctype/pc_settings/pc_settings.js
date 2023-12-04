// Copyright (c) 2023, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('PC Settings', {
	refresh: function(frm) {
		frm.fields_dict["zero_tax_template_for_purchase_expenses"].grid.get_field("zero_tax_template").get_query = function(doc, cdt, cdn) {
			var d = locals[cdt][cdn];
			return {
				filters: {
					'company': d.company
				}
			}
		}
		frm.fields_dict["default_petty_cash_accounts"].grid.get_field("petty_cash_account").get_query = function(doc, cdt, cdn) {
			var d = locals[cdt][cdn];
			return {
				filters: {
					"is_group": 0,
					"account_type": "Payable",
					'company': d.company
				}
			}
		}		
	}

});
