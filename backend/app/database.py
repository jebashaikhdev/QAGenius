import sqlite3
from pathlib import Path
import json

DB_PATH = Path(__file__).resolve().parent.parent / "qagenius.db"

def get_db_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    connection = get_db_connection()
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS test_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requirement TEXT NOT NULL,
                analysis TEXT NOT NULL,
                test_cases TEXT NOT NULL,
                review TEXT NOT NULL,
                agent_status TEXT NOT NULL,
                human_approved INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS test_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_run_id INTEGER NOT NULL,
                case_id TEXT NOT NULL,
                scenario TEXT NOT NULL,
                preconditions TEXT,
                steps TEXT NOT NULL,
                test_data TEXT,
                expected_result TEXT NOT NULL,
                test_type TEXT,
                priority TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (test_run_id)
                    REFERENCES test_runs(id),

                UNIQUE (test_run_id, case_id)
            )
            """
        )
        
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS jira_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_case_id INTEGER NOT NULL UNIQUE,
                jira_issue_key TEXT NOT NULL UNIQUE,
                jira_issue_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (test_case_id)
                    REFERENCES test_cases(id)
            )
            """
        )
        
        columns = connection.execute(
            "PRAGMA table_info(test_runs)"
        ).fetchall()
        
        column_names = [column["name"] for column in columns]
        
        if "human_decision" not in column_names:
            connection.execute(
                """
                ALTER TABLE test_runs
                ADD COLUMN human_decision TEXT DEFAULT 'pending'
                """
            )
        connection.execute(
            """
            UPDATE test_runs
            SET human_decision = 'approved'
            WHERE human_approved = 1
            """
        )

        existing_runs = connection.execute(
            "SELECT id, test_cases FROM test_runs"
        ).fetchall()

        for run in existing_runs:
            existing_cases = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM test_cases
                WHERE test_run_id = ?
                """,
                (run["id"],)
            ).fetchone()["total"]

            if existing_cases > 0:
                continue

            raw_test_cases = run["test_cases"]

            if not raw_test_cases or not raw_test_cases.strip():
                print(
                    f"Skipping migration for test run {run['id']}: "
                    "empty test case data."
                )
                continue

            try:
                cases = json.loads(raw_test_cases)

                # Support both a JSON array and a wrapped JSON object.
                if isinstance(cases, dict):
                    cases = cases.get("test_cases", [])

                if not isinstance(cases, list):
                    raise ValueError("Test cases must be a JSON array.")

                for case in cases:
                    connection.execute(
                        """
                        INSERT OR IGNORE INTO test_cases (
                            test_run_id,
                            case_id,
                            scenario,
                            preconditions,
                            steps,
                            test_data,
                            expected_result,
                            test_type,
                            priority
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            run["id"],
                            case["id"],
                            case["scenario"],
                            case["preconditions"],
                            json.dumps(case["steps"]),
                            case["test_data"],
                            case["expected_result"],
                            case["test_type"],
                            case["priority"]
                        )
                    )

            except (json.JSONDecodeError, ValueError, KeyError, TypeError) as e:
                print(
                    f"Could not migrate test run {run['id']}: {e}"
                )

        
        connection.commit()
        
    finally:
        connection.close()


def save_test_run(
    requirement: str,
    analysis: str,
    test_cases: str,
    review: str,
    agent_status: str
):
    connection = get_db_connection()

    try:
        # Insert the parent test run
        cursor = connection.execute(
            """
            INSERT INTO test_runs (
                requirement,
                analysis,
                test_cases,
                review,
                agent_status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                requirement,
                analysis,
                test_cases,
                review,
                agent_status
            )
        )

        test_run_id = cursor.lastrowid

        # Convert the JSON string into individual test cases
        cases = json.loads(test_cases)

        # Insert each test case with its parent test_run_id
        for case in cases:
            connection.execute(
                """
                INSERT INTO test_cases (
                    test_run_id,
                    case_id,
                    scenario,
                    preconditions,
                    steps,
                    test_data,
                    expected_result,
                    test_type,
                    priority
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    test_run_id,
                    case["id"],
                    case["scenario"],
                    case["preconditions"],
                    json.dumps(case["steps"]),
                    case["test_data"],
                    case["expected_result"],
                    case["test_type"],
                    case["priority"]
                )
            )

        connection.commit()

        return test_run_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

        
def get_test_run(
    test_run_id: int
):
    connection = get_db_connection()
    
    try:
        row =  connection.execute(
            "SELECT * FROM test_runs WHERE id = ?",
            (test_run_id,)
        ).fetchone()
        
        return dict(row) if row else None
    
    finally:
        connection.close()
        
        
def get_test_cases(test_run_id: int):
    connection = get_db_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM test_cases
            WHERE test_run_id = ?
            ORDER BY id
            """,
            (test_run_id,)
        ).fetchall()

        test_cases = []

        for row in rows:
            case = dict(row)
            case["steps"] = json.loads(case["steps"])
            test_cases.append(case)

        return test_cases

    finally:
        connection.close()

def approve_test_run(test_run_id: int):
    connection = get_db_connection()
    
    try:
        cursor = connection.execute(
            """
            UPDATE test_runs
            SET human_approved = 1,
                human_decision = 'approved'
            WHERE id = ?
            AND agent_status = 'approved'
            AND human_decision = 'pending'
            """,
            (test_run_id,)
        )
        
        connection.commit()
        
        return cursor.rowcount > 0
    
    finally:
        connection.close()
        
def reject_test_run(test_run_id: int):
    connection = get_db_connection()
    try:
        cursor = connection.execute(
            """
            UPDATE test_runs
            SET human_approved = 0,
                human_decision = "rejected"
            WHERE id = ?
            AND human_decision = 'pending'
            """,
            (test_run_id,)
        )
            
        connection.commit()
            
        return cursor.rowcount > 0
    finally:
        connection.close()


# Save the Jira issue mapping       
def save_jira_issue(test_case_id: int, jira_issue_key: str, jira_issue_id: str):
    connection = get_db_connection()

    try:
        connection.execute(
            """
            INSERT INTO jira_issues (
                test_case_id,
                jira_issue_key,
                jira_issue_id
            )
            VALUES (?, ?, ?)
            """,
            (test_case_id, jira_issue_key, jira_issue_id)
        )

        connection.commit()

    finally:
        connection.close()

# Retrieve existing Jira mappings
def get_jira_issue(test_case_id: int):
    connection = get_db_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM jira_issues
            WHERE test_case_id = ?
            """,
            (test_case_id,)
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()
        