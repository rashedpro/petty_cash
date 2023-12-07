// Copyright (c) 2023, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('PC Request', {
	refresh:function (frm) {
	if (frm.doc.docstatus==1) {
		frm.add_custom_button('Make PE', () => {
			make_payment_entry(frm)
		})
	}	
	},
	date: function(frm) {
		set_previous_balance(frm)
	},
	employee: function(frm) {
		set_previous_balance(frm)
	},
	company: function(frm) {
		set_previous_balance(frm)
		set_petty_cash_account(frm)
	}		
});

function set_petty_cash_account(frm) {
	if(frm.doc.company) {
		frappe.call({
			method: "petty_cash.petty_cash.doctype.pc_request.pc_request.fetch_petty_cash_account",
			args: {
				company: frm.doc.company,
			},
			callback: function(r, rt) {
				if(r.message) {
					 frm.set_value("petty_cash_account", r.message);
				}else{
					frm.set_value("petty_cash_account", null);
				}
			}
		})
	}		
}

function set_previous_balance(frm) {
	if(frm.doc.date && frm.doc.employee && frm.doc.company && frm.doc.petty_cash_account) {
		frappe.call({
			method: "petty_cash.petty_cash.doctype.pc_request.pc_request.get_balance_of_account_for_an_employee",
			args: {
				company: frm.doc.company,
				account:frm.doc.petty_cash_account,
				party: frm.doc.employee,
				to_date: frm.doc.date,
				party_type: 'Employee',
			},
			callback: function(r, rt) {
				if(r.message) {
					console.log(r,r.message)
					 frm.set_value("previous_balance", r.message);
				}
			}
		})
	}	
}

function make_payment_entry(frm) {
	// todo : open new window
	// todo: copy project from request?
	// todo : Payment Status
		frappe.model.with_doctype("Payment Entry", function() {
			let payment_entry = frappe.model.get_new_doc("Payment Entry");
			payment_entry.payment_type = 'Pay';
			payment_entry.company = frm.doc.company;
			payment_entry.party_type = 'Employee';
			payment_entry.party = frm.doc.employee;
			payment_entry.paid_to = frm.doc.petty_cash_account;
			payment_entry.custom_pc_request_reference = frm.doc.name;
			payment_entry.paid_amount = frm.doc.total_amount;
			payment_entry.project=frm.doc.project || '';

			// frappe.open_in_new_tab =true
			// frappe.route_options=payment_entry
			frappe.set_route("Form", "Payment Entry",payment_entry.name);		
			setTimeout(() => {
				payment_entry.party = frm.doc.employee;
				payment_entry.party_name=frm.doc.employee_name;
			
			},200);

		})

}