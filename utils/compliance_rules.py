# Super simple hardcoded rules — interns can edit this easily

DOCUMENTS = {
    "Individual": ["Passport", "National ID", "Address Proof"],
    "Business": ["Company Registration Certificate", "Tax Registration", "Director KYC"]
}

COMPLIANCE_RULES = {
    ("India", "Business", "Fintech / Payments"): ["PCI DSS", "RBI KYC"],
    ("India", "Business", "Insurance"): ["PCI DSS", "RBI KYC"],
    ("India", "Individual", "Fintech / Payments"): ["RBI KYC"],
    ("India", "Individual", "Insurance"): ["RBI KYC"],

    ("USA", "Business", "Fintech / Payments"): ["PCI DSS", "SOC 2"],
    ("USA", "Business", "Insurance"): ["SOC 2"],
    ("USA", "Individual", "eSIM / Telecom"): ["FCC Rules", "SOC 2"],
    ("USA", "Business", "eSIM / Telecom"): ["FCC Rules", "SOC 2", "PCI DSS"],

    ("Singapore", "Business", "Fintech / Payments"): ["PCI DSS", "MAS Guidelines"],
    ("Singapore", "Individual", "Fintech / Payments"): ["MAS Guidelines"],

    ("UAE", "Business", "Fintech / Payments"): ["PCI DSS"],
    ("UAE", "Business", "Insurance"): ["SOC 2"],

    ("Germany (EU)", "Business", "Fintech / Payments"): ["PCI DSS", "GDPR"],
    ("Germany (EU)", "Individual", "Fintech / Payments"): ["GDPR"],
    ("Germany (EU)", "Business", "Insurance"): ["GDPR", "SOC 2"],
    ("Germany (EU)", "Individual", "Insurance"): ["GDPR", "SOC 2"],
}

DEFAULT_COMPLIANCE = {
    "Fintech / Payments": ["PCI DSS"],
    "Insurance": ["SOC 2"],
    "eSIM / Telecom": []
}

def get_requirements(country, entity_type, product_category):
    key = (country, entity_type, product_category)
    compliance = COMPLIANCE_RULES.get(key, DEFAULT_COMPLIANCE.get(product_category, []))

    if country == "Germany (EU)" and "GDPR" not in compliance:
        compliance.append("GDPR")

    compliance = sorted(set(compliance))
    documents = sorted(DOCUMENTS[entity_type])

    return {
        "documents": documents,
        "compliance": compliance
    }