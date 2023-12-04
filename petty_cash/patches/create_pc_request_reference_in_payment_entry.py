import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    print("Creating Petty Cash Request Reference in Payment Entry...")
    custom_fields = {
        "Payment Entry": [
            dict(
                fieldname="custom_pc_request_reference",
                label="PC Request Reference",
                fieldtype="Link",
                options="PC Request",
                insert_after="reference_no",
                read_only=1,
                is_custom_field=1,
                is_system_generated=0,
                translatable=0
            )
        ]
    }

    create_custom_fields(custom_fields, update=True)