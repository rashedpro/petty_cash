// Copyright (c) 2023, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('PC Expense Type', {
	refresh: function(frm) {
		frm.fields_dict["accounts"].grid.get_field("default_account").get_query = function(doc, cdt, cdn) {
			var d = locals[cdt][cdn];
			return {
				filters: {
					"is_group": 0,
					"root_type": frm.doc.deferred_expense_account ? "Asset" : "Expense",
					'company': d.company
				}
			}
		}
	}
})