import os
import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("finguard.database")

MYSQL_HOST = os.environ.get("MYSQL_HOST", "")
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "loan")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))

_memory_records: List[Dict[str, Any]] = []
_next_id = 1
_mysql_ok = False


def _mysql_configured() -> bool:
    return bool(MYSQL_HOST.strip())


def db_active() -> bool:
    """True when connected to MySQL; False when using in-memory demo storage."""
    return _mysql_ok


def get_db_connection(include_db: bool = True):
    """Establishes connection to the MySQL server."""
    import mysql.connector

    if include_db:
        return mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            port=MYSQL_PORT,
        )
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        port=MYSQL_PORT,
    )


def _init_mysql() -> bool:
    global _mysql_ok
    logger.info(f"Initializing MySQL database '{MYSQL_DATABASE}'...")

    conn = get_db_connection(include_db=False)
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE}")
    conn.commit()
    cursor.close()
    conn.close()

    conn = get_db_connection(include_db=True)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loananalysis (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            income DOUBLE NOT NULL,
            loan_amount DOUBLE NOT NULL,
            credit_score INT NOT NULL,
            debt_to_income DOUBLE NOT NULL,
            employment_status VARCHAR(100) NOT NULL,
            notes TEXT,
            tenure INT NOT NULL,
            risk_score DOUBLE NOT NULL,
            risk_grade VARCHAR(100) NOT NULL,
            compliance_status VARCHAR(50) NOT NULL,
            compliance_logs TEXT,
            audit_report TEXT,
            audit_mode VARCHAR(20) NOT NULL DEFAULT 'rule_based',
            created_at VARCHAR(100) NOT NULL
        ) ENGINE=InnoDB
    """)

    cursor.execute("SHOW COLUMNS FROM loananalysis LIKE 'audit_mode'")
    if not cursor.fetchone():
        cursor.execute(
            "ALTER TABLE loananalysis ADD COLUMN audit_mode VARCHAR(20) NOT NULL DEFAULT 'rule_based'"
        )

    conn.commit()
    cursor.close()
    conn.close()
    _mysql_ok = True
    logger.info(f"MySQL table 'loananalysis' ready in database '{MYSQL_DATABASE}'.")
    return True


def init_db() -> bool:
    """Initialize MySQL when configured; otherwise use in-memory storage (HF demo mode)."""
    global _mysql_ok

    if not _mysql_configured():
        _mysql_ok = False
        logger.info("MySQL not configured — using in-memory storage (demo mode).")
        return False

    try:
        return _init_mysql()
    except Exception as exc:
        logger.warning(f"MySQL unavailable, using in-memory storage: {exc}")
        _mysql_ok = False
        return False


def save_loan_analysis(
    name: str,
    income: float,
    loan_amount: float,
    credit_score: int,
    debt_to_income: float,
    employment_status: str,
    notes: str,
    tenure: int,
    risk_score: float,
    risk_grade: str,
    compliance_status: str,
    compliance_logs: List[Dict[str, Any]],
    audit_report: str,
    audit_mode: str = "rule_based",
) -> int:
    """Inserts a new loan analysis record."""
    global _next_id
    created_at = datetime.now().isoformat()

    if _mysql_ok:
        conn = get_db_connection()
        cursor = conn.cursor()
        compliance_logs_json = json.dumps(compliance_logs)
        query = """
            INSERT INTO loananalysis (
                name, income, loan_amount, credit_score, debt_to_income,
                employment_status, notes, tenure, risk_score, risk_grade, compliance_status,
                compliance_logs, audit_report, audit_mode, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            name, income, loan_amount, credit_score, debt_to_income,
            employment_status, notes, tenure, risk_score, risk_grade, compliance_status,
            compliance_logs_json, audit_report, audit_mode, created_at,
        )
        cursor.execute(query, params)
        row_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return row_id

    record_id = _next_id
    _next_id += 1
    _memory_records.append({
        "id": record_id,
        "name": name,
        "income": income,
        "loan_amount": loan_amount,
        "credit_score": credit_score,
        "debt_to_income": debt_to_income,
        "employment_status": employment_status,
        "notes": notes,
        "tenure": tenure,
        "risk_score": risk_score,
        "risk_grade": risk_grade,
        "compliance_status": compliance_status,
        "compliance_logs": list(compliance_logs),
        "audit_report": audit_report,
        "audit_mode": audit_mode,
        "created_at": created_at,
    })
    return record_id


def fetch_all_applicants() -> List[Dict[str, Any]]:
    """Returns all records sorted by date descending."""
    if _mysql_ok:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM loananalysis ORDER BY created_at DESC")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows

    return sorted(_memory_records, key=lambda r: r["created_at"], reverse=True)


def fetch_applicant_details(record_id: int) -> Optional[Dict[str, Any]]:
    """Returns details for a single record, parsing compliance logs when needed."""
    if _mysql_ok:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM loananalysis WHERE id = %s", (record_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            return None
        try:
            row["compliance_logs"] = json.loads(row["compliance_logs"]) if row["compliance_logs"] else []
        except Exception:
            row["compliance_logs"] = []
        return row

    for row in _memory_records:
        if row["id"] == record_id:
            return dict(row)
    return None


def delete_applicant_record(record_id: int) -> bool:
    """Deletes a record by ID."""
    global _memory_records

    if _mysql_ok:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM loananalysis WHERE id = %s", (record_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete record {record_id}: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    before = len(_memory_records)
    _memory_records = [r for r in _memory_records if r["id"] != record_id]
    return len(_memory_records) < before
