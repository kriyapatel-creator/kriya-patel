import pandas as pd


# Simplified demo checklist based on the CTD module structure.
# This is intentionally configurable and is NOT a regulatory
# determination of submission compliance.

CTD_CHECKLIST = {
    "Module 1 - Administrative Information": [
        "Regional administrative information",
        "Application forms",
        "Prescribing information",
        "Product information"
    ],

    "Module 2 - CTD Summaries": [
        "CTD introduction",
        "Quality overall summary",
        "Nonclinical overview",
        "Clinical overview",
        "Nonclinical written summaries",
        "Clinical summary"
    ],

    "Module 3 - Quality": [
        "Drug substance information",
        "Drug product information",
        "Manufacturing process",
        "Control of drug substance",
        "Control of drug product",
        "Stability information"
    ],

    "Module 4 - Nonclinical Study Reports": [
        "Pharmacology studies",
        "Pharmacokinetic studies",
        "Toxicology studies"
    ],

    "Module 5 - Clinical Study Reports": [
        "Clinical pharmacology studies",
        "Clinical efficacy studies",
        "Clinical safety studies",
        "Post-marketing experience",
        "Clinical study reports"
    ]
}


def create_checklist_dataframe():
    rows = []

    for module, sections in CTD_CHECKLIST.items():

        for section in sections:

            rows.append({
                "Module": module,
                "Section": section,
                "Present": False
            })

    return pd.DataFrame(rows)


def check_submission(dossier_items):
    """
    Compare supplied dossier items against the configured
    CTD checklist.
    """

    checklist = create_checklist_dataframe()

    supplied = {
        str(item).strip().lower()
        for item in dossier_items
    }

    checklist["Present"] = checklist["Section"].apply(
        lambda x: x.lower() in supplied
    )

    checklist["Status"] = checklist["Present"].apply(
        lambda x: "Complete" if x else "Missing"
    )

    return checklist


def calculate_module_scores(checklist):
    """
    Calculate completeness percentage for each CTD module.
    """

    scores = []

    for module, group in checklist.groupby("Module"):

        total = len(group)
        completed = group["Present"].sum()

        percentage = (
            (completed / total) * 100
            if total > 0
            else 0
        )

        scores.append({
            "Module": module,
            "Completed": int(completed),
            "Total": total,
            "Completeness": round(percentage, 1)
        })

    return pd.DataFrame(scores)


def generate_gap_report(checklist):
    """
    Return only missing dossier sections.
    """

    gaps = checklist[
        checklist["Status"] == "Missing"
    ][["Module", "Section"]].copy()

    gaps["Priority"] = gaps["Module"].apply(
        lambda x: (
            "High"
            if "Module 3" in x or "Module 5" in x
            else "Medium"
        )
    )

    return gaps
