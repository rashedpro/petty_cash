// Copyright (c) 2023, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('PC Clearance', {
	// refresh: function(frm) {

	// }
	

});


frappe.ui.form.on('PC Clearance Detail', {
	project: function(frm,cdt,cdn) {
		let row=locals[cdt][cdn]
		if (row.project) {
			frappe.db.get_value('Project', row.project, 'cost_center')
			.then(r => {
				if (r.message && r.message.cost_center) {
					let cost_center=r.message.cost_center
					frappe.model.set_value(cdt, cdn, 'cost_center', cost_center);
					frm.refresh_field("clearance_details")
				}else{
					frappe.db.get_value('Company', company, 'cost_center')
					.then(r => {
						if (r.message && r.message.cost_center) {
							let cost_center=r.message.cost_center
							frappe.model.set_value(cdt, cdn, 'cost_center', cost_center);
							frm.refresh_field("clearance_details")
						}
					})
				}
			})
		}
	},
	before_clearance_details_remove: function(frm,cdt,cdn) {
		let row=locals[cdt][cdn]
		console.log(row)
		if (row.is_non_stock_expense_type==0) {
			remove_rows_from_stock_item_dialog(frm,row.idx)
		}
	},	
	is_non_stock_expense_type: function(frm,cdt,cdn) {
		let row=locals[cdt][cdn]
		if (row.is_non_stock_expense_type==1) {
			remove_rows_from_stock_item_dialog(frm,row.idx)
		}
	},
	// clearance_details_add: function(frm,cdt,cdn) {
	// 	if (frm.is_new()==1) {
	// 		frm.save()
	// 	}
	// },
	add_item: function(frm,cdt,cdn) {
		debugger
		let row=locals[cdt][cdn]

		if (row.expense_type) {
			frappe.db.get_value('PC Expense Type', row.expense_type, 'is_non_stock_expense_type')
			.then(r => {
				console.log(r.message) // Open
				let is_non_stock_expense_type=r.message.is_non_stock_expense_type
				if (is_non_stock_expense_type==0) {
					// frm.trigger("show_add_stock_item_dialog")
					
					show_add_stock_item_dialog(frm,row.name,row.idx,row.expense_type)
				} else {
					let msg=__("{0} is non stock item, so nothing to add.", [row.expense_type])
					frappe.show_alert(msg, 5);
					
				}
			})		
		}		

	}
});

function remove_rows_from_stock_item_dialog(frm,clearance_detail_row_idx){
	debugger
    var tbl = frm.doc.stock_item_details || [];
    var i = tbl.length;
    while (i--) {
        if(frm.doc.stock_item_details[i].clearance_detail_row_idx == clearance_detail_row_idx) {
            frm.get_field("stock_item_details").grid.grid_rows[i].remove();
            frm.refresh_field("stock_item_details")
        }
    }

}
// todo : await thing
function get_cost_center(project,company) {
	frappe.db.get_value('Project', project, 'cost_center')
	.then(r => {
		let cost_center=undefined
		if (r.message && r.message.cost_center) {
			cost_center=r.message.cost_center
			return cost_center
		}else{
			frappe.db.get_value('Company', company, 'cost_center')
			.then(r => {
				if (r.message && r.message.cost_center) {
					cost_center=r.message.cost_center
					return cost_center
				}
			})
		}
	})		
}

function show_add_stock_item_dialog(frm,clearance_row_name,clearance_row_idx,clearance_row_expense_type) {
	

debugger
		let data = [];
		const dialog = new frappe.ui.Dialog({
			title: __(""),
			fields: [
				{
					fieldname: "dialog_stock_item_details",
					fieldtype: "Table",
					label: __("Enter Stock Items For Row <b>{0}</b> : <b>{1}</b> ",[clearance_row_idx,clearance_row_expense_type]),
					data: data,
					in_place_edit: true,
					cannot_add_rows: false,
					get_data: () => {
						return data;
					},
					fields: [
					{
						fieldtype:'Link',
						options: 'Item',
						fieldname:"item_code",
						label: __("item_code"),
						in_list_view: 1,
						reqd: 1,
						// onchange: () => fetch_pos_payment_methods()
					}, 
					// {
					// 	fieldtype:'Data',
					// 	fieldname:"item_name",
					// 	label: __("Item Name"),
					// 	in_list_view: 1,
					// 	read_only: 1
					// }, 
					{
						fieldtype:'Int',
						fieldname:"qty",
						label: __("qty"),
						in_list_view: 1,
					}, 
					{
						fieldtype:'Currency',
						fieldname:"rate",
						label: __("rate"),
						in_list_view: 1,
					}, 										
					{
						fieldtype:'Link',
						options: 'Warehouse',
						in_list_view: 1,
						label: __("warehouse"),
						fieldname: 'warehouse',
						reqd: 1,
						get_query: () => {
							return {
								filters: {
									company: frm.doc.company,
									is_group: 0
								}
							}
						}
					}, 
					// {
					// 	fieldtype:'Currency',
					// 	in_list_view: 1,
					// 	label: __("total"),
					// 	fieldname: 'total',
					// 	read_only: 1
					// },
					{
						fieldtype:'Data',
						fieldname:"clearance_detail_row_idx",
						in_list_view: 0,
						hidden: 1
					}				
				]
				},
				// {
				// 	fieldtype: 'HTML',
				// 	options: "<b> New Journal Entry will be posted for the difference amount </b>"
				// }
			],
			primary_action: () => {
				const args = dialog.get_values()["dialog_stock_item_details"];

				args.forEach(d => {
					// frappe.model.set_value("PC Stock Item Expense Detail",stock_item_details,
					// 	"difference_account", d.difference_account);
						let row = frm.add_child("stock_item_details");
						row.item_code = d.item_code;
						// row.item_name=
						row.qty = d.qty;
						row.rate = d.rate;
						row.total = d.qty*d.rate;
						row.warehouse = d.warehouse;	
						row.clearance_detail_row_idx=clearance_row_idx			
				});

				// me.reconcile_payment_entries();
				frm.refresh_field('stock_item_details')
				dialog.hide();
			},
			primary_action_label: __('Done')
		});

		if (frm.doc.stock_item_details) {
			frm.doc.stock_item_details.forEach(d => {
				if (d.clearance_detail_row_idx==clearance_row_idx) {
					dialog.fields_dict.dialog_stock_item_details.df.data.push({
						'item_code': d.item_code,
						// 'item_name': d.item_name,
						'qty': d.qty,
						'rate': d.rate,
						'warehouse': d.warehouse,
						// 'total': d.total,
						'clearance_detail_row_idx':d.clearance_detail_row_idx
					});
				}
			});
			data = dialog.fields_dict.dialog_stock_item_details.df.data;
			
		}


		
		dialog.fields_dict.dialog_stock_item_details.grid.refresh();
		dialog.show();

}	