import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    print("Creating Max Balance For Petty Cash in Employee...")
    custom_fields = {
        "Employee": [
            dict(
                fieldname="maximum_balance_for_petty_cash_cf",
                label="Max Balance For Petty Cash",
                fieldtype="Currency",
                insert_after="branch",
                is_custom_field=1,
                is_system_generated=0,
                translatable=0
            )
        ]
    }

    create_custom_fields(custom_fields, update=True)