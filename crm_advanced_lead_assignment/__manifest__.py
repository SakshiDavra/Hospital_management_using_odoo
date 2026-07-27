{
    "name": "CRM Advanced Lead Assignment",
    "version": "19.0.1.0.0",
    "category": "Sales/CRM",
    "summary": "Advanced Lead Assignment with Round Robin and Rule Engine",
    "author" : "abcd",
    "license": "LGPL-3",
    "depends": [
        "crm",
        "base_address_extended",
        "hr_skills",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/crm_assignment_rule_views.xml",
    ],
    "installable": True,
    "application": False,
}