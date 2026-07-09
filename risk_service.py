import os
import json
import logging
import urllib.request
import ssl
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger("finguard.risk_service")

# Bypass SSL certificates for standard HTTP API calls
_SSL_CONTEXT = ssl._create_unverified_context()

GEMINI_CHAT_MODEL = "models/gemini-1.5-flash"
API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
ANNUAL_INTEREST_RATE = 10.5  # Standard rate used for EMI and DTI calculations

def calculate_emi(loan_amount: float, tenure_years: int) -> float:
    """Calculates monthly EMI using standard amortization formula."""
    if loan_amount <= 0 or tenure_years <= 0:
        return 0.0
    monthly_rate = ANNUAL_INTEREST_RATE / 12 / 100
    total_months = tenure_years * 12
    factor = (1 + monthly_rate) ** total_months
    return (loan_amount * monthly_rate * factor) / (factor - 1)

def calculate_dti(
    income: float,
    loan_amount: float,
    tenure_years: int,
    existing_monthly_debt: float = 0.0
) -> float:
    """DTI (%) = (existing monthly debt + new loan EMI) / monthly gross income × 100."""
    monthly_income = income / 12
    if monthly_income <= 0:
        return 100.0
    emi = calculate_emi(loan_amount, tenure_years)
    total_monthly_debt = max(0.0, existing_monthly_debt) + emi
    dti = (total_monthly_debt / monthly_income) * 100
    return round(min(100.0, max(0.0, dti)), 1)

def calculate_credit_risk(
    income: float,
    loan_amount: float,
    credit_score: int,
    debt_to_income: float,
    employment_status: str
) -> Tuple[float, str]:
    """Calculates statistical Credit Risk score (0-100) and assigns grade (A-D)."""
    
    # 1. Credit Score Component (40% weight)
    # 850 is perfect (0 risk), 300 is worst (100 risk)
    credit_risk = max(0.0, min(100.0, (800 - credit_score) / (800 - 400) * 100))
    
    # 2. Debt-to-Income Component (35% weight)
    # Under 20% is perfect, above 50% is maximum risk
    dti_risk = max(0.0, min(100.0, (debt_to_income - 15) / (50 - 15) * 100))
    
    # 3. Loan-to-Income (LTI) Component (25% weight)
    # Safe LTI ratio is < 3.0. Above 6.0 is extremely risky.
    lti_ratio = loan_amount / max(1000.0, income)
    lti_risk = max(0.0, min(100.0, (lti_ratio - 1.5) / (6.0 - 1.5) * 100))
    
    # 4. Employment Multipliers & Add-ons
    employment_penalty = 0.0
    status_lower = employment_status.lower()
    if "unemployed" in status_lower:
        employment_penalty = 30.0
    elif "student" in status_lower:
        employment_penalty = 15.0
    elif "self-employed" in status_lower:
        employment_penalty = 10.0
        
    # Calculate Weighted score
    raw_score = (0.40 * credit_risk) + (0.35 * dti_risk) + (0.25 * lti_risk) + employment_penalty
    risk_score = round(max(0.0, min(100.0, raw_score)), 1)
    
    # Assign Grade
    if risk_score < 25.0:
        risk_grade = "Low Risk (Grade A)"
    elif risk_score < 50.0:
        risk_grade = "Moderate Risk (Grade B)"
    elif risk_score < 75.0:
        risk_grade = "High Risk (Grade C)"
    else:
        risk_grade = "Critical Risk (Grade D)"
        
    return risk_score, risk_grade

def run_compliance_checks(
    income: float,
    loan_amount: float,
    credit_score: int,
    debt_to_income: float,
    employment_status: str
) -> List[Dict[str, str]]:
    """Runs rule-based compliance audits and returns check logs."""
    checks = []
    
    # Check 1: DTI limit check
    if debt_to_income > 45.0:
        checks.append({
            "check_name": "Debt-to-Income Benchmark Audit",
            "status": "FLAGGED",
            "details": f"Debt-to-income ratio ({debt_to_income}%) exceeds regulatory safe threshold of 45.0%."
        })
    else:
        checks.append({
            "check_name": "Debt-to-Income Benchmark Audit",
            "status": "PASSED",
            "details": f"DTI ratio ({debt_to_income}%) is within standard compliance limits."
        })
        
    # Check 2: LTI Loan size validation
    lti_ratio = loan_amount / max(1.0, income)
    if lti_ratio > 8.0:
        checks.append({
            "check_name": "Loan-to-Income Outlier Audit",
            "status": "FLAGGED",
            "details": f"Requested loan is {round(lti_ratio, 1)}x annual income. Exceeds standard AML structuring limit (8.0x)."
        })
    else:
        checks.append({
            "check_name": "Loan-to-Income Outlier Audit",
            "status": "PASSED",
            "details": f"Loan amount is {round(lti_ratio, 1)}x annual income, which satisfies standard size thresholds."
        })
        
    # Check 3: Subprime Credit rating
    if credit_score < 580:
        checks.append({
            "check_name": "Subprime Risk Threshold Audit",
            "status": "FLAGGED",
            "details": f"Credit score ({credit_score}) lies in the subprime category (<580), flagging high structural default risk."
        })
    else:
        checks.append({
            "check_name": "Subprime Risk Threshold Audit",
            "status": "PASSED",
            "details": f"Credit score ({credit_score}) satisfies prime lending standards."
        })
        
    return checks

def generate_audit_report(
    name: str,
    income: float,
    loan_amount: float,
    credit_score: int,
    debt_to_income: float,
    employment_status: str,
    notes: str,
    risk_score: float,
    risk_grade: str,
    checks: List[Dict[str, str]],
    api_key: Optional[str] = None
) -> Tuple[str, str]:
    """Generates an audit report. Returns (report_text, audit_mode) where audit_mode is 'ai' or 'rule_based'."""
    
    # Formulate unstructured prompt
    flagged_checks = [c["check_name"] for c in checks if c["status"] == "FLAGGED"]
    flags_str = ", ".join(flagged_checks) if flagged_checks else "None"
    
    prompt = f"""You are FinGuard-AI, a loan auditor.
Analyze the following personal loan application files for default risks, anti-money laundering (AML) compliance, and potential fraudulent indicators.

APPLICANT PROFILE:
- Name: {name}
- Annual Income: ₹{income:,.2f}
- Requested Loan: ₹{loan_amount:,.2f}
- Credit Score: {credit_score}
- Debt-to-Income Ratio: {debt_to_income}%
- Employment Status: {employment_status}
- Self-Reported Notes: "{notes or 'None provided.'}"

COMPLIANCE CHECKS:
- Statistical Risk Score: {risk_score}/100 ({risk_grade})
- Flagged Compliance Rules: {flags_str}

AUDIT INSTRUCTIONS:
1. Write a professional, detailed audit report.
2. Structure it with clear markdown headers:
   ### 1. Executive Summary
   ### 2. Credit Risk Analysis
   ### 3. AML & Verification Audit (Inspect self-reported notes for cash-laundering patterns, suspicious shell companies, crypto speculations, or overseas transfers)
   ### 4. Audit Recommendation (State clearly: "APPROVED", "FLAGGED FOR MANUAL AUDIT", or "REJECTED" with bulleted compliance reasons)
3. Be objective, precise, and professional.
"""

    env_key = api_key or os.environ.get("GEMINI_API_KEY")
    if env_key:
        logger.info("Connecting to Gemini API to synthesize audit report...")
        report = _call_gemini_api(prompt, env_key)
        if report:
            return report, "ai"

    # Rule-based fallback when no API key or AI call fails
    logger.info("Using rule-based audit report engine...")
    report = _generate_offline_report(name, income, loan_amount, credit_score, debt_to_income, employment_status, notes, risk_score, risk_grade, checks)
    return report, "rule_based"

def _call_gemini_api(prompt: str, api_key: str) -> Optional[str]:
    url = f"{API_BASE_URL}/{GEMINI_CHAT_MODEL}:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, 
        data=data, 
        method="POST", 
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, context=_SSL_CONTEXT) as response:
            result = json.loads(response.read().decode("utf-8"))
            candidates = result.get("candidates", [])
            if candidates:
                return candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return None
    except Exception as e:
        logger.error(f"Gemini loan audit API call failed: {e}")
        return None

def _generate_offline_report(
    name: str,
    income: float,
    loan_amount: float,
    credit_score: int,
    debt_to_income: float,
    employment_status: str,
    notes: str,
    risk_score: float,
    risk_grade: str,
    checks: List[Dict[str, str]]
) -> str:
    """Compiles rule-based compliance reviews when AI is unavailable."""
    
    flagged_checks = [c for c in checks if c["status"] == "FLAGGED"]
    has_flags = len(flagged_checks) > 0
    notes_lower = notes.lower() if notes else ""
    
    # Audit applicant text notes for keyword anomalies
    red_flag_notes = []
    if "crypto" in notes_lower or "bitcoin" in notes_lower:
        red_flag_notes.append("Self-reported interest in cryptocurrency speculation represents non-business, high-volatility capitalization.")
    if "overseas" in notes_lower or "transfer" in notes_lower or "offshore" in notes_lower:
        red_flag_notes.append("Mention of cross-border transfers requires detailed foreign tax identification (FATCA) checking.")
    if "cash" in notes_lower or "anonymous" in notes_lower:
        red_flag_notes.append("Unverifiable cash flows present immediate compliance risks under Anti-Money Laundering (AML) standards.")
        
    report = f"### FinGuard Audit Report for {name}\n\n"
    
    report += "### 1. Executive Summary\n"
    report += f"A compliance audit was run on applicant **{name}** for a requested loan amount of **₹{loan_amount:,.2f}**. "
    if has_flags or red_flag_notes:
        report += f"The application contains **{len(flagged_checks) + len(red_flag_notes)} compliance flags** and a statistical credit risk grade of **{risk_grade}**. Manual audit intervention is required.\n\n"
    else:
        report += f"The application is clean with **0 compliance flags** and a statistical risk grade of **{risk_grade}**. Recommendation leans towards standard underwriting approval.\n\n"
        
    report += "### 2. Credit Risk Analysis\n"
    report += f"- **Risk Assessment Score**: {risk_score}/100. Grade: {risk_grade}.\n"
    report += f"- **Debt Service Capacity**: With an annual income of ₹{income:,.2f} and a Debt-to-Income ratio of {debt_to_income}%, the borrower's monthly residual income is estimated as "
    monthly_inc = income / 12
    monthly_debt = monthly_inc * (debt_to_income / 100)
    report += f"₹{(monthly_inc - monthly_debt):,.2f} after existing debt obligations.\n"
    if credit_score < 600:
        report += "- **Credit Integrity Warning**: Low credit rating increases statistical default probability during economic contractions.\n"
    else:
        report += "- **Credit rating status**: Stable prime rating maintains safety thresholds.\n"
        
    report += "\n### 3. AML & Verification Audit\n"
    if red_flag_notes or (loan_amount / max(1.0, income)) > 8.0:
        report += "⚠️ **RED FLAGS DETECTED IN APPLICATION DETAILS**:\n"
        for flag in red_flag_notes:
            report += f"- *Flagged*: {flag}\n"
        if (loan_amount / max(1.0, income)) > 8.0:
            report += f"- *Flagged*: High Loan-to-Income ratio ({round(loan_amount/max(1.0, income), 1)}x) exceeds AML monitoring benchmarks.\n"
    else:
        report += "- **Anti-Money Laundering (AML)**: Notes search returned no cash-concealment or structuring triggers. Mapped parameters appear verified.\n"
        
    report += "\n### 4. Audit Recommendation\n"
    if risk_score > 60.0 or len(flagged_checks) >= 2 or len(red_flag_notes) > 0:
        report += "❌ **RECOMMENDATION: REJECTED & FLAGGED FOR MANUAL AUDIT**\n\n"
        report += "**Primary Violations**:\n"
        for check in flagged_checks:
            report += f"- *Compliance Failure*: {check['details']}\n"
        for flag in red_flag_notes:
            report += f"- *Suspicious Activity Alert*: {flag}\n"
    elif has_flags:
        report += "⚠️ **RECOMMENDATION: FLAGGED FOR SECONDARY REVIEW**\n\n"
        report += "**Audited Warnings**:\n"
        for check in flagged_checks:
            report += f"- *Warning*: {check['details']}\n"
    else:
        report += "✅ **RECOMMENDATION: APPROVED**\n\n"
        report += "Applicant passes all risk scoring limits and regulatory audit guidelines. Standard lending protocols apply.\n"
        
    return report
