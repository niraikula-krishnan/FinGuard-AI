// FinGuard-AI — Static demo (localStorage, no backend required for HF free hosting)
const STORAGE_KEY = "finguard_applicants";
let nextId = 1;
let activeApplicantId = null;
let applicantsData = [];
let activeFilter = "all";
let searchQuery = "";

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

function loadFromStorage() {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        applicantsData = raw ? JSON.parse(raw) : [];
        nextId = applicantsData.reduce((max, r) => Math.max(max, r.id || 0), 0) + 1;
    } catch {
        applicantsData = [];
        nextId = 1;
    }
}

function saveToStorage() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(applicantsData));
}

document.addEventListener("DOMContentLoaded", () => {
    loadFromStorage();
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
    if (searchInput) {
        searchInput.addEventListener("input", (e) => {
            searchQuery = e.target.value.toLowerCase().trim();
            filterAndRenderTable();
        });
    }
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

function fetchApplicants() {
    loadFromStorage();
    dbCounter.textContent = `${applicantsData.length} Records`;
    filterAndRenderTable();
}

function filterAndRenderTable() {
    let filtered = applicantsData;
    if (activeFilter === "passed") filtered = filtered.filter(app => app.compliance_status === "PASSED");
    else if (activeFilter === "flagged") filtered = filtered.filter(app => app.compliance_status === "FLAGGED");
    if (searchQuery) filtered = filtered.filter(app => app.name.toLowerCase().includes(searchQuery));
    renderLedgerTable(filtered);
}

function renderLedgerTable(applicants) {
    if (applicants.length === 0) {
        applicantRows.innerHTML = `<tr><td colspan="7" class="table-placeholder">No matching applicants found.</td></tr>`;
        return;
    }
    applicantRows.innerHTML = applicants.map(app => {
        const riskVal = app.risk_score;
        let riskColorClass = riskVal >= 50 ? "risk-high" : riskVal >= 25 ? "risk-moderate" : "risk-low";
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
            </tr>`;
    }).join("");
    lucide.createIcons();
}

function updateFinancialsRealtime() {
    const loanVal = parseFloat(loanAmountInput.value) || 0;
    const tenureVal = parseInt(tenureInput.value) || 0;
    const incomeVal = parseFloat(incomeInput.value) || 0;
    const existingDebtVal = parseFloat(existingDebtInput.value) || 0;
    if (loanVal <= 0 || tenureVal <= 0) emiDisplayInput.value = "₹0";
    else emiDisplayInput.value = `₹${Math.round(RiskEngine.calculateEmi(loanVal, tenureVal)).toLocaleString()}`;
    const dti = RiskEngine.calculateDti(incomeVal, loanVal, tenureVal, existingDebtVal);
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
    submitBtn.disabled = true;
    submitBtn.textContent = "Auditing...";
    try {
        const record = RiskEngine.processApplication(payload, nextId++);
        applicantsData.unshift(record);
        saveToStorage();
        nameInput.value = "";
        incomeInput.value = "";
        loanAmountInput.value = "";
        creditScoreInput.value = "";
        existingDebtInput.value = "0";
        notesInput.value = "";
        tenureInput.value = "5";
        updateFinancialsRealtime();
        fetchApplicants();
        inspectApplicant(record.id);
    } catch (err) {
        alert(`Error: ${err.message}`);
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<i data-lucide="calculator" class="btn-icon"></i> Calculate & Audit Risk`;
        lucide.createIcons();
    }
}

function inspectApplicant(id) {
    activeApplicantId = id;
    deactivateRowSelection();
    const rowEl = document.getElementById(`row-${id}`);
    if (rowEl) {
        rowEl.classList.add("inspect-row-selected");
        const btn = rowEl.querySelector(".row-actions .row-btn");
        if (btn) btn.classList.add("inspect-btn-active");
    }
    const data = applicantsData.find(a => a.id === id);
    if (!data) return;
    inspectName.textContent = data.name;
    inspectGrade.textContent = data.risk_grade;
    const riskScore = data.risk_score;
    inspectGrade.className = "risk-badge " + (riskScore >= 50 ? "grade-red" : riskScore >= 25 ? "grade-yellow" : "grade-green");
    const circumference = 251.2;
    riskGaugeFill.style.strokeDashoffset = circumference - (circumference * (riskScore / 100));
    riskGaugeText.textContent = `${riskScore}%`;
    riskGaugeFill.className.baseVal = "gauge-fill";
    riskGaugeFill.classList.add(riskScore >= 50 ? "risk-red" : riskScore >= 25 ? "risk-yellow" : "risk-green");
    complianceChecksList.innerHTML = data.compliance_logs.map(log => {
        const flagged = log.status === "FLAGGED";
        return `<div class="check-item ${flagged ? "flagged" : "passed"}"><i data-lucide="${flagged ? "alert-triangle" : "shield-check"}"></i><div><span style="font-weight:600;display:block;margin-bottom:2px;">${log.check_name}</span><span style="color:var(--text-muted);font-size:0.7rem;">${log.details}</span></div></div>`;
    }).join("");
    inspectReportText.innerHTML = parseMarkdown(data.audit_report);
    inspectReportMode.textContent = "Rule-based Report";
    inspectReportMode.className = "badge badge-rule-based";
    auditInspector.classList.remove("hidden");
    auditInspector.scrollIntoView({ behavior: "smooth" });
    lucide.createIcons();
}

function deleteApplicant(e, id) {
    e.stopPropagation();
    if (!confirm("Delete this applicant?")) return;
    applicantsData = applicantsData.filter(a => a.id !== id);
    saveToStorage();
    if (id === activeApplicantId) {
        auditInspector.classList.add("hidden");
        activeApplicantId = null;
    }
    fetchApplicants();
}

function deactivateRowSelection() {
    document.querySelectorAll(".applicant-row-tr").forEach(tr => tr.classList.remove("inspect-row-selected"));
    document.querySelectorAll(".row-actions .row-btn").forEach(btn => btn.classList.remove("inspect-btn-active"));
}

function escapeHtml(text) {
    if (!text) return "";
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function parseMarkdown(text) {
    let html = text.replace(/\*\*([\s\S]*?)\*\*/g, "<strong>$1</strong>").replace(/\*([\s\S]*?)\*/g, "<em>$1</em>");
    const lines = html.split("\n");
    let inList = false;
    const out = [];
    lines.forEach(line => {
        const trimmed = line.trim();
        if (trimmed.startsWith("###")) {
            if (inList) { out.push("</ul>"); inList = false; }
            out.push(`<h3>${trimmed.replace("###", "").trim()}</h3>`);
        } else if (trimmed.startsWith("-")) {
            if (!inList) { out.push("<ul>"); inList = true; }
            out.push(`<li>${trimmed.substring(1).trim()}</li>`);
        } else {
            if (inList) { out.push("</ul>"); inList = false; }
            if (trimmed) out.push(`<p>${trimmed}</p>`);
        }
    });
    if (inList) out.push("</ul>");
    return out.join("");
}
