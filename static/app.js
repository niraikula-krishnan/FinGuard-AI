// FinGuard-AI Frontend Controller

const ANNUAL_INTEREST_RATE = 10.5;

let activeApplicantId = null;
let applicantsData = [];
let activeFilter = 'all';
let searchQuery = '';

// DOM Elements
const loanForm = document.getElementById("loan-form");
const nameInput = document.getElementById("name");
const incomeInput = document.getElementById("income");
const loanAmountInput = document.getElementById("loan_amount");
const creditScoreInput = document.getElementById("credit_score");
const existingDebtInput = document.getElementById("existing_monthly_debt");
const dtiDisplayInput = document.getElementById("debt_to_income");
const employmentSelect = document.getElementById("employment_status");
const notesInput = document.getElementById("notes");
const tenureInput = document.getElementById("tenure");
const emiDisplayInput = document.getElementById("emi_display");
const submitBtn = document.getElementById("submit-btn");

const dbCounter = document.getElementById("db-counter");
const applicantRows = document.getElementById("applicant-rows");
const searchInput = document.getElementById("search-input");
const filterTabs = document.querySelectorAll(".filter-tab");

const auditInspector = document.getElementById("audit-inspector");
const closeInspectorBtn = document.getElementById("close-inspector-btn");
const inspectName = document.getElementById("inspect-name");
const inspectGrade = document.getElementById("inspect-grade");
const riskGaugeFill = document.getElementById("risk-gauge-fill");
const riskGaugeText = document.getElementById("risk-gauge-text");
const complianceChecksList = document.getElementById("compliance-checks-list");
const inspectReportText = document.getElementById("inspect-report-text");
const inspectReportMode = document.getElementById("inspect-report-mode");

function calculateEmi(loanAmount, tenureYears) {
    if (loanAmount <= 0 || tenureYears <= 0) return 0;
    const monthlyRate = ANNUAL_INTEREST_RATE / 12 / 100;
    const totalMonths = tenureYears * 12;
    const factor = Math.pow(1 + monthlyRate, totalMonths);
    return (loanAmount * monthlyRate * factor) / (factor - 1);
}

function calculateDti(annualIncome, loanAmount, tenureYears, existingMonthlyDebt) {
    const monthlyIncome = annualIncome / 12;
    if (monthlyIncome <= 0) return 100;
    const emi = calculateEmi(loanAmount, tenureYears);
    const totalMonthlyDebt = Math.max(0, existingMonthlyDebt) + emi;
    const dti = (totalMonthlyDebt / monthlyIncome) * 100;
    return Math.min(100, Math.max(0, dti));
}

// Initial Setup
document.addEventListener("DOMContentLoaded", () => {
    fetchApplicants();

    [loanAmountInput, tenureInput, incomeInput, existingDebtInput].forEach(el => {
        if (el) el.addEventListener("input", updateFinancialsRealtime);
    });
    updateFinancialsRealtime();
    
    closeInspectorBtn.addEventListener("click", () => {
        auditInspector.classList.add("hidden");
        activeApplicantId = null;
        deactivateRowSelection();
    });
    
    // Wire up search bar
    if (searchInput) {
        searchInput.addEventListener("input", (e) => {
            searchQuery = e.target.value.toLowerCase().trim();
            filterAndRenderTable();
        });
    }
    
    // Wire up filter tabs
    filterTabs.forEach(tab => {
        tab.addEventListener("click", () => {
            filterTabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            activeFilter = tab.getAttribute("data-filter");
            filterAndRenderTable();
        });
    });
});

loanForm.addEventListener("submit", handleFormSubmit);

async function fetchApplicants() {
    try {
        const response = await fetch("/api/applicants");
        if (!response.ok) throw new Error("Failed to retrieve ledger ledger.");
        const data = await response.json();
        
        applicantsData = data;
        dbCounter.textContent = `${data.length} Records`;
        filterAndRenderTable();
    } catch (err) {
        console.error(err);
        applicantRows.innerHTML = `<tr><td colspan="7" class="table-placeholder" style="color:var(--color-red);">Error loading applicant records: ${err.message}</td></tr>`;
    }
}

function filterAndRenderTable() {
    let filtered = applicantsData;
    
    // 1. Filter by Passed/Flagged tabs
    if (activeFilter === "passed") {
        filtered = filtered.filter(app => app.compliance_status === "PASSED");
    } else if (activeFilter === "flagged") {
        filtered = filtered.filter(app => app.compliance_status === "FLAGGED");
    }
    
    // 2. Filter by search name query
    if (searchQuery) {
        filtered = filtered.filter(app => app.name.toLowerCase().includes(searchQuery));
    }
    
    renderLedgerTable(filtered);
}

function renderLedgerTable(applicants) {
    if (applicants.length === 0) {
        applicantRows.innerHTML = `<tr><td colspan="7" class="table-placeholder">No matching applicants found.</td></tr>`;
        return;
    }
    
    applicantRows.innerHTML = applicants.map(app => {
        const riskVal = app.risk_score;
        let riskColorClass = "risk-low";
        if (riskVal >= 50.0) {
            riskColorClass = "risk-high";
        } else if (riskVal >= 25.0) {
            riskColorClass = "risk-moderate";
        }
        
        const complClass = app.compliance_status === "PASSED" ? "badge-passed" : "badge-flagged";
        const isInspected = app.id === activeApplicantId ? "inspect-btn-active" : "";
        
        return `
            <tr id="row-${app.id}" class="applicant-row-tr">
                <td><strong>${escapeHtml(app.name)}</strong></td>
                <td>₹${app.loan_amount.toLocaleString()}</td>
                <td>${app.credit_score}</td>
                <td>${app.debt_to_income}%</td>
                <td class="risk-cell ${riskColorClass}">${riskVal}%</td>
                <td><span class="badge ${complClass}">${app.compliance_status}</span></td>
                <td>
                    <div class="row-actions">
                        <button class="row-btn ${isInspected}" onclick="inspectApplicant(${app.id})" title="Inspect Audit Report"><i data-lucide="eye"></i></button>
                        <button class="row-btn delete-btn-hover" onclick="deleteApplicant(event, ${app.id})" title="Delete Application"><i data-lucide="trash-2"></i></button>
                    </div>
                </td>
            </tr>
        `;
    }).join("");
    
    lucide.createIcons();
}

function updateFinancialsRealtime() {
    const loanVal = parseFloat(loanAmountInput.value) || 0;
    const tenureVal = parseInt(tenureInput.value) || 0;
    const incomeVal = parseFloat(incomeInput.value) || 0;
    const existingDebtVal = parseFloat(existingDebtInput.value) || 0;

    if (loanVal <= 0 || tenureVal <= 0) {
        emiDisplayInput.value = "₹0";
    } else {
        const emi = calculateEmi(loanVal, tenureVal);
        emiDisplayInput.value = `₹${Math.round(emi).toLocaleString()}`;
    }

    const dti = calculateDti(incomeVal, loanVal, tenureVal, existingDebtVal);
    dtiDisplayInput.value = incomeVal > 0 ? `${dti.toFixed(1)}%` : "—";
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const payload = {
        name: nameInput.value.trim(),
        income: parseFloat(incomeInput.value),
        loan_amount: parseFloat(loanAmountInput.value),
        credit_score: parseInt(creditScoreInput.value),
        existing_monthly_debt: parseFloat(existingDebtInput.value) || 0,
        employment_status: employmentSelect.value,
        notes: notesInput.value.trim(),
        tenure: parseInt(tenureInput.value)
    };
    
    // Disable inputs
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span class="spinner" style="width:14px; height:14px; border-width:2px; display:inline-block; vertical-align:middle; margin-right:6px;"></span> Auditing...`;
    
    try {
        const response = await fetch("/api/applicants", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to submit loan files.");
        }
        
        const result = await response.json();
        
        // Reset inputs
        nameInput.value = "";
        incomeInput.value = "";
        loanAmountInput.value = "";
        creditScoreInput.value = "";
        existingDebtInput.value = "0";
        notesInput.value = "";
        tenureInput.value = "5";
        updateFinancialsRealtime();
        
        // Reload Table
        await fetchApplicants();
        
        // Auto open the new applicant report
        inspectApplicant(result.id);
        
    } catch (err) {
        console.error(err);
        alert(`Error calculating risk model: ${err.message}`);
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<i data-lucide="calculator" class="btn-icon"></i> Calculate & Audit Risk`;
        lucide.createIcons();
    }
}

async function inspectApplicant(id) {
    activeApplicantId = id;
    
    // Highlight table row
    deactivateRowSelection();
    const rowEl = document.getElementById(`row-${id}`);
    if (rowEl) {
        rowEl.classList.add("inspect-row-selected");
        // Find inspect button and highlight
        const btn = rowEl.querySelector(".row-actions .row-btn");
        if (btn) btn.classList.add("inspect-btn-active");
    }
    
    try {
        const response = await fetch(`/api/applicants/${id}`);
        if (!response.ok) throw new Error("Failed to load audit file.");
        const data = await response.json();
        
        // Update labels
        inspectName.textContent = data.name;
        inspectGrade.textContent = data.risk_grade;
        
        // Update risk grade color badge
        const riskScore = data.risk_score;
        inspectGrade.className = "risk-badge";
        if (riskScore >= 75.0) {
            inspectGrade.classList.add("grade-red");
        } else if (riskScore >= 50.0) {
            inspectGrade.classList.add("grade-red");
        } else if (riskScore >= 25.0) {
            inspectGrade.classList.add("grade-yellow");
        } else {
            inspectGrade.classList.add("grade-green");
        }
        
        // Update Risk SVG Gauge
        // Radius = 40. Circumference = 2 * PI * R = 251.2
        const circumference = 251.2;
        const offset = circumference - (circumference * (riskScore / 100));
        riskGaugeFill.style.strokeDashoffset = offset;
        riskGaugeText.textContent = `${riskScore}%`;
        
        // Update Gauge Fill Class Color
        riskGaugeFill.className.baseVal = "gauge-fill";
        if (riskScore >= 50.0) {
            riskGaugeFill.classList.add("risk-red");
        } else if (riskScore >= 25.0) {
            riskGaugeFill.classList.add("risk-yellow");
        } else {
            riskGaugeFill.classList.add("risk-green");
        }
        
        // Populate compliance checklist
        complianceChecksList.innerHTML = data.compliance_logs.map(log => {
            const isFlagged = log.status === "FLAGGED";
            const iconName = isFlagged ? "alert-triangle" : "shield-check";
            const itemClass = isFlagged ? "flagged" : "passed";
            return `
                <div class="check-item ${itemClass}">
                    <i data-lucide="${iconName}"></i>
                    <div>
                        <span style="font-weight:600; display:block; margin-bottom:2px;">${log.check_name}</span>
                        <span style="color:var(--text-muted); font-size:0.7rem;">${log.details}</span>
                    </div>
                </div>
            `;
        }).join("");
        
        // Populate Markdown audit text
        inspectReportText.innerHTML = parseMarkdown(data.audit_report);

        const auditMode = data.audit_mode || "rule_based";
        const isAiReport = auditMode === "ai";
        inspectReportMode.textContent = isAiReport ? "AI Report" : "Rule-based Report";
        inspectReportMode.className = isAiReport ? "badge badge-ai" : "badge badge-rule-based";
        
        // Reveal Inspector Card
        auditInspector.classList.remove("hidden");
        
        // Auto scroll viewport down to see inspector easily
        auditInspector.scrollIntoView({ behavior: "smooth" });
        
        lucide.createIcons();
    } catch (err) {
        console.error(err);
        alert(`Error opening report: ${err.message}`);
    }
}

async function deleteApplicant(e, id) {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this applicant file from ledger database?")) {
        return;
    }
    
    try {
        const response = await fetch(`/api/applicants/${id}`, { method: "DELETE" });
        if (!response.ok) throw new Error("Delete failed.");
        
        if (id === activeApplicantId) {
            auditInspector.classList.add("hidden");
            activeApplicantId = null;
        }
        
        await fetchApplicants();
    } catch (err) {
        console.error(err);
        alert(`Error deleting record: ${err.message}`);
    }
}

function deactivateRowSelection() {
    document.querySelectorAll(".applicant-row-tr").forEach(tr => {
        tr.classList.remove("inspect-row-selected");
    });
    document.querySelectorAll(".row-actions .row-btn").forEach(btn => {
        btn.classList.remove("inspect-btn-active");
    });
}

function escapeHtml(text) {
    if (!text) return "";
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Simple Client Markdown Parsing
function parseMarkdown(text) {
    let html = text;
    // Bold: **text**
    html = html.replace(/\*\*([\s\S]*?)\*\*/g, '<strong>$1</strong>');
    // Italic: *text*
    html = html.replace(/\*([\s\S]*?)\*/g, '<em>$1</em>');
    
    // Headers mapping
    const lines = html.split("\n");
    let inList = false;
    let listHtml = [];
    
    lines.forEach(line => {
        const trimmed = line.trim();
        if (trimmed.startsWith("###")) {
            if (inList) {
                listHtml.push('</ul>');
                inList = false;
            }
            listHtml.push(`<h3>${trimmed.replace("###", "").trim()}</h3>`);
        } else if (trimmed.startsWith("-") || trimmed.startsWith("*")) {
            if (!inList) {
                listHtml.push('<ul>');
                inList = true;
            }
            listHtml.push(`<li>${trimmed.substring(1).trim()}</li>`);
        } else {
            if (inList) {
                listHtml.push('</ul>');
                inList = false;
            }
            if (trimmed !== "") {
                listHtml.push(`<p>${trimmed}</p>`);
            }
        }
    });
    
    if (inList) {
        listHtml.push('</ul>');
    }
    
    return listHtml.join("");
}
