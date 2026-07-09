import os
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

import database
import risk_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("finguard")

load_dotenv()

app = FastAPI(
    title="FinGuard-AI API",
    description="Loan applicant risk assessment and AML compliance audit server.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_db():
    mode = "MySQL" if database.init_db() else "in-memory (demo)"
    logger.info(f"Database ready: {mode}")


class ApplicantSubmitRequest(BaseModel):
    name: str
    income: float
    loan_amount: float
    credit_score: int
    existing_monthly_debt: float = 0.0
    employment_status: str
    notes: Optional[str] = ""
    tenure: Optional[int] = 5
    api_key: Optional[str] = None


@app.get("/api/applicants")
async def list_applicants():
    """Returns a list of all applicants from the MySQL database."""
    try:
        return database.fetch_all_applicants()
    except Exception as e:
        logger.error(f"Failed to fetch applicants: {e}")
        raise HTTPException(status_code=500, detail="Database retrieval failure.")


@app.get("/api/applicants/{applicant_id}")
async def get_applicant_details(applicant_id: int):
    """Returns full details, compliance checks, and audit report for one applicant."""
    try:
        details = database.fetch_applicant_details(applicant_id)
        if not details:
            raise HTTPException(status_code=404, detail="Applicant record not found.")
        return details
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch applicant details: {e}")
        raise HTTPException(status_code=500, detail="Database fetch error.")


@app.post("/api/applicants")
async def submit_applicant(request: ApplicantSubmitRequest):
    """Calculates risk, runs compliance checks, generates audit report, and saves to database."""
    try:
        name = request.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Applicant name cannot be empty.")

        tenure = request.tenure or 5
        debt_to_income = risk_service.calculate_dti(
            income=request.income,
            loan_amount=request.loan_amount,
            tenure_years=tenure,
            existing_monthly_debt=request.existing_monthly_debt,
        )

        risk_score, risk_grade = risk_service.calculate_credit_risk(
            income=request.income,
            loan_amount=request.loan_amount,
            credit_score=request.credit_score,
            debt_to_income=debt_to_income,
            employment_status=request.employment_status
        )

        checks = risk_service.run_compliance_checks(
            income=request.income,
            loan_amount=request.loan_amount,
            credit_score=request.credit_score,
            debt_to_income=debt_to_income,
            employment_status=request.employment_status
        )

        flagged_count = sum(1 for c in checks if c["status"] == "FLAGGED")
        compliance_status = "FLAGGED" if flagged_count > 0 else "PASSED"

        audit_report, audit_mode = risk_service.generate_audit_report(
            name=name,
            income=request.income,
            loan_amount=request.loan_amount,
            credit_score=request.credit_score,
            debt_to_income=debt_to_income,
            employment_status=request.employment_status,
            notes=request.notes,
            risk_score=risk_score,
            risk_grade=risk_grade,
            checks=checks,
            api_key=request.api_key
        )

        record_id = database.save_loan_analysis(
            name=name,
            income=request.income,
            loan_amount=request.loan_amount,
            credit_score=request.credit_score,
            debt_to_income=debt_to_income,
            employment_status=request.employment_status,
            notes=request.notes,
            tenure=tenure,
            risk_score=risk_score,
            risk_grade=risk_grade,
            compliance_status=compliance_status,
            compliance_logs=checks,
            audit_report=audit_report,
            audit_mode=audit_mode
        )

        return {
            "id": record_id,
            "name": name,
            "risk_score": risk_score,
            "risk_grade": risk_grade,
            "debt_to_income": debt_to_income,
            "compliance_status": compliance_status,
            "audit_mode": audit_mode
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit loan application: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/applicants/{applicant_id}")
async def delete_applicant(applicant_id: int):
    """Deletes an applicant record."""
    try:
        success = database.delete_applicant_record(applicant_id)
        if not success:
            raise HTTPException(status_code=404, detail="Applicant not found or delete failed.")
        return {"success": True, "message": f"Applicant {applicant_id} deleted successfully."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deletion failed: {e}")
        raise HTTPException(status_code=500, detail="Database deletion error.")


static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:
    logger.warning(f"Static directory not found at: {static_dir}")
