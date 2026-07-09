// Client-side risk engine (mirrors risk_service.py for HF static demo)
const RiskEngine = (() => {
    const ANNUAL_INTEREST_RATE = 10.5;

    function calculateEmi(loanAmount, tenureYears) {
        if (loanAmount <= 0 || tenureYears <= 0) return 0;
        const monthlyRate = ANNUAL_INTEREST_RATE / 12 / 100;
        const totalMonths = tenureYears * 12;
        const factor = Math.pow(1 + monthlyRate, totalMonths);
        return (loanAmount * monthlyRate * factor) / (factor - 1);
    }

    function calculateDti(income, loanAmount, tenureYears, existingMonthlyDebt = 0) {
        const monthlyIncome = income / 12;
        if (monthlyIncome <= 0) return 100;
        const emi = calculateEmi(loanAmount, tenureYears);
        const totalMonthlyDebt = Math.max(0, existingMonthlyDebt) + emi;
        const dti = (totalMonthlyDebt / monthlyIncome) * 100;
        return Math.round(Math.min(100, Math.max(0, dti)) * 10) / 10;
    }

    function calculateCreditRisk(income, loanAmount, creditScore, debtToIncome, employmentStatus) {
        const creditRisk = Math.max(0, Math.min(100, (800 - creditScore) / (800 - 400) * 100));
        const dtiRisk = Math.max(0, Math.min(100, (debtToIncome - 15) / (50 - 15) * 100));
        const ltiRatio = loanAmount / Math.max(1000, income);
        const ltiRisk = Math.max(0, Math.min(100, (ltiRatio - 1.5) / (6.0 - 1.5) * 100));

        let employmentPenalty = 0;
        const status = employmentStatus.toLowerCase();
        if (status.includes("unemployed")) employmentPenalty = 30;
        else if (status.includes("student")) employmentPenalty = 15;
        else if (status.includes("self-employed")) employmentPenalty = 10;

        const rawScore = 0.4 * creditRisk + 0.35 * dtiRisk + 0.25 * ltiRisk + employmentPenalty;
        const riskScore = Math.round(Math.max(0, Math.min(100, rawScore)) * 10) / 10;

        let riskGrade;
        if (riskScore < 25) riskGrade = "Low Risk (Grade A)";
        else if (riskScore < 50) riskGrade = "Moderate Risk (Grade B)";
        else if (riskScore < 75) riskGrade = "High Risk (Grade C)";
        else riskGrade = "Critical Risk (Grade D)";

        return { riskScore, riskGrade };
    }

    function runComplianceChecks(income, loanAmount, creditScore, debtToIncome) {
        const checks = [];
        if (debtToIncome > 45) {
            checks.push({ check_name: "Debt-to-Income Benchmark Audit", status: "FLAGGED", details: `Debt-to-income ratio (${debtToIncome}%) exceeds regulatory safe threshold of 45.0%.` });
        } else {
            checks.push({ check_name: "Debt-to-Income Benchmark Audit", status: "PASSED", details: `DTI ratio (${debtToIncome}%) is within standard compliance limits.` });
        }
        const ltiRatio = loanAmount / Math.max(1, income);
        if (ltiRatio > 8) {
            checks.push({ check_name: "Loan-to-Income Outlier Audit", status: "FLAGGED", details: `Requested loan is ${ltiRatio.toFixed(1)}x annual income. Exceeds standard AML structuring limit (8.0x).` });
        } else {
            checks.push({ check_name: "Loan-to-Income Outlier Audit", status: "PASSED", details: `Loan amount is ${ltiRatio.toFixed(1)}x annual income, which satisfies standard size thresholds.` });
        }
        if (creditScore < 580) {
            checks.push({ check_name: "Subprime Risk Threshold Audit", status: "FLAGGED", details: `Credit score (${creditScore}) lies in the subprime category (<580), flagging high structural default risk.` });
        } else {
            checks.push({ check_name: "Subprime Risk Threshold Audit", status: "PASSED", details: `Credit score (${creditScore}) satisfies prime lending standards.` });
        }
        return checks;
    }

    function generateOfflineReport(name, income, loanAmount, creditScore, debtToIncome, notes, riskScore, riskGrade, checks) {
        const flaggedChecks = checks.filter(c => c.status === "FLAGGED");
        const hasFlags = flaggedChecks.length > 0;
        const notesLower = (notes || "").toLowerCase();
        const redFlagNotes = [];
        if (notesLower.includes("crypto") || notesLower.includes("bitcoin")) {
            redFlagNotes.push("Self-reported interest in cryptocurrency speculation represents non-business, high-volatility capitalization.");
        }
        if (notesLower.includes("overseas") || notesLower.includes("transfer") || notesLower.includes("offshore")) {
            redFlagNotes.push("Mention of cross-border transfers requires detailed foreign tax identification (FATCA) checking.");
        }
        if (notesLower.includes("cash") || notesLower.includes("anonymous")) {
            redFlagNotes.push("Unverifiable cash flows present immediate compliance risks under Anti-Money Laundering (AML) standards.");
        }

        let report = `### FinGuard Audit Report for ${name}\n\n`;
        report += "### 1. Executive Summary\n";
        report += `A compliance audit was run on applicant **${name}** for a requested loan amount of **₹${loanAmount.toLocaleString()}**. `;
        if (hasFlags || redFlagNotes.length) {
            report += `The application contains **${flaggedChecks.length + redFlagNotes.length} compliance flags** and a statistical credit risk grade of **${riskGrade}**. Manual audit intervention is required.\n\n`;
        } else {
            report += `The application is clean with **0 compliance flags** and a statistical risk grade of **${riskGrade}**. Recommendation leans towards standard underwriting approval.\n\n`;
        }
        report += "### 2. Credit Risk Analysis\n";
        report += `- **Risk Assessment Score**: ${riskScore}/100. Grade: ${riskGrade}.\n`;
        const monthlyInc = income / 12;
        const monthlyDebt = monthlyInc * (debtToIncome / 100);
        report += `- **Debt Service Capacity**: With an annual income of ₹${income.toLocaleString()} and a Debt-to-Income ratio of ${debtToIncome}%, the borrower's monthly residual income is estimated as ₹${(monthlyInc - monthlyDebt).toLocaleString(undefined, {maximumFractionDigits: 2})} after existing debt obligations.\n`;
        report += creditScore < 600
            ? "- **Credit Integrity Warning**: Low credit rating increases statistical default probability during economic contractions.\n"
            : "- **Credit rating status**: Stable prime rating maintains safety thresholds.\n";
        report += "\n### 3. AML & Verification Audit\n";
        if (redFlagNotes.length || loanAmount / Math.max(1, income) > 8) {
            report += "⚠️ **RED FLAGS DETECTED IN APPLICATION DETAILS**:\n";
            redFlagNotes.forEach(flag => { report += `- *Flagged*: ${flag}\n`; });
            if (loanAmount / Math.max(1, income) > 8) {
                report += `- *Flagged*: High Loan-to-Income ratio (${(loanAmount / income).toFixed(1)}x) exceeds AML monitoring benchmarks.\n`;
            }
        } else {
            report += "- **Anti-Money Laundering (AML)**: Notes search returned no cash-concealment or structuring triggers. Mapped parameters appear verified.\n";
        }
        report += "\n### 4. Audit Recommendation\n";
        if (riskScore > 60 || flaggedChecks.length >= 2 || redFlagNotes.length > 0) {
            report += "❌ **RECOMMENDATION: REJECTED & FLAGGED FOR MANUAL AUDIT**\n\n**Primary Violations**:\n";
            flaggedChecks.forEach(c => { report += `- *Compliance Failure*: ${c.details}\n`; });
            redFlagNotes.forEach(f => { report += `- *Suspicious Activity Alert*: ${f}\n`; });
        } else if (hasFlags) {
            report += "⚠️ **RECOMMENDATION: FLAGGED FOR SECONDARY REVIEW**\n\n**Audited Warnings**:\n";
            flaggedChecks.forEach(c => { report += `- *Warning*: ${c.details}\n`; });
        } else {
            report += "✅ **RECOMMENDATION: APPROVED**\n\nApplicant passes all risk scoring limits and regulatory audit guidelines. Standard lending protocols apply.\n";
        }
        return report;
    }

    function processApplication(payload, id) {
        const debtToIncome = calculateDti(payload.income, payload.loan_amount, payload.tenure, payload.existing_monthly_debt);
        const { riskScore, riskGrade } = calculateCreditRisk(payload.income, payload.loan_amount, payload.credit_score, debtToIncome, payload.employment_status);
        const checks = runComplianceChecks(payload.income, payload.loan_amount, payload.credit_score, debtToIncome);
        const complianceStatus = checks.some(c => c.status === "FLAGGED") ? "FLAGGED" : "PASSED";
        const auditReport = generateOfflineReport(payload.name, payload.income, payload.loan_amount, payload.credit_score, debtToIncome, payload.notes, riskScore, riskGrade, checks);
        return {
            id,
            name: payload.name,
            income: payload.income,
            loan_amount: payload.loan_amount,
            credit_score: payload.credit_score,
            debt_to_income: debtToIncome,
            employment_status: payload.employment_status,
            notes: payload.notes,
            tenure: payload.tenure,
            risk_score: riskScore,
            risk_grade: riskGrade,
            compliance_status: complianceStatus,
            compliance_logs: checks,
            audit_report: auditReport,
            audit_mode: "rule_based",
            created_at: new Date().toISOString()
        };
    }

    return { calculateEmi, calculateDti, processApplication };
})();
