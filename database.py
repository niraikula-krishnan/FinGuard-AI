import mysql.connector
import os
import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger("finguard.database")

# Read connection parameters from environment variables
MYSQL_HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "loan")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))

def get_db_connection(include_db: bool = True):
    """Establishes connection to the MySQL server."""
    if include_db:
        return mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            port=MYSQL_PORT
        )
    else:
        return mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            port=MYSQL_PORT
        )

def init_db():
    """Initializes the MySQL database and table structures if missing."""
    logger.info(f"Initializing MySQL database '{MYSQL_DATABASE}'...")
    
    # 1. Connect without selecting database to create it
    try:
        conn = get_db_connection(include_db=False)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE}")
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to check/create MySQL database: {e}")
        raise RuntimeError(f"MySQL connection error. Make sure MySQL is running on {MYSQL_HOST}:{MYSQL_PORT}. Detail: {e}")

    # 2. Connect with selected database and create the single table
    conn = get_db_connection(include_db=True)
    cursor = conn.cursor()

    # Create the single simplified table 'loananalysis'
    cursor.execute(f"""
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
    logger.info(f"MySQL table 'loananalysis' initialized successfully inside database '{MYSQL_DATABASE}'.")

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
    audit_mode: str = "rule_based"
) -> int:
    """Inserts a new loan analysis record into the 'loananalysis' table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    created_at = datetime.now().isoformat()
    
    # Serialize logs list to JSON string for single-column storage
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
        compliance_logs_json, audit_report, audit_mode, created_at
    )
              
    cursor.execute(query, params)
    row_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return row_id

def fetch_all_applicants() -> List[Dict[str, Any]]:
    """Returns all records sorted by date descending."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM loananalysis ORDER BY created_at DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def fetch_applicant_details(record_id: int) -> Optional[Dict[str, Any]]:
    """Returns details for a single record, parsing the compliance logs JSON."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM loananalysis WHERE id = %s", (record_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not row:
        return None
        
    # Deserialize compliance logs from JSON string back to Python list
    try:
        row["compliance_logs"] = json.loads(row["compliance_logs"]) if row["compliance_logs"] else []
    except Exception:
        row["compliance_logs"] = []
        
    return row

def delete_applicant_record(record_id: int) -> bool:
    """Deletes a record by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM loananalysis WHERE id = %s", (record_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to delete record {record_id}: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()
