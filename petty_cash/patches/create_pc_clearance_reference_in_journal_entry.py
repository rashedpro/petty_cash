import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    print("Creating Petty Cash Clearance Reference in Journal Entry...")
    custom_fields = {
        "Journal Entry": [
            dict(
                fieldname="custom_pc_clearance_reference",
                label="PC Clearance Reference",
                fieldtype="Link",
                options="PC Clearance",
                insert_after="inter_company_journal_entry_reference",
                read_only=1,
                is_custom_field=1,
                is_system_generated=0,
                translatable=0
            )
        ]
    }

    create_custom_fields(custom_fields, update=True)