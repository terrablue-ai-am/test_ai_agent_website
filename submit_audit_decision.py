import functions_framework
import pymysql
import sqlalchemy
import os
from flask import jsonify, make_response, request
from google.cloud.sql.connector import Connector, IPTypes

# Database connection setup
def connect_with_connector() -> sqlalchemy.engine.base.Engine:
    os.environ["INSTANCE_CONNECTION_NAME"] = 'support-assist-384720:us-central1:support-assist-v2'
    os.environ["DB_USER"] = 'swapnil@terrablue.ai'
    os.environ["DB_PASS"] = 'swapnil@terrablue.ai'
    os.environ["DB_NAME"] = 'sav2_responses'

    instance_connection_name = os.environ["INSTANCE_CONNECTION_NAME"]
    db_user = os.environ["DB_USER"]
    db_pass = os.environ["DB_PASS"]
    db_name = os.environ["DB_NAME"]

    ip_type = IPTypes.PRIVATE if os.environ.get("PRIVATE_IP") else IPTypes.PUBLIC
    connector = Connector(ip_type)

    def getconn():
        return connector.connect(
            instance_connection_name,
            "pymysql",
            user=db_user,
            password=db_pass,
            db=db_name
        )

    pool = sqlalchemy.create_engine(
        "mysql+pymysql://",
        creator=getconn,
    )
    return pool

# Function to update both Feedback_Collection and the main table
def update_feedback_in_db(table, feedback_data):
    pool = connect_with_connector()

    try:
        with pool.connect() as conn:
            # Update Feedback_Collection (using cid = cfid)
            conn.execute(
                sqlalchemy.text(
                    """
                    UPDATE `sav2_responses_staging`.`Feedback_Collection`
                    SET audit_category = :audit_category, audit_description = :audit_description
                    WHERE cid = :cfid
                    """
                ),
                parameters=feedback_data
            )

            # Update the main table (using cfid)
            conn.execute(
                sqlalchemy.text(
                    f"""
                    UPDATE `sav2_responses`.`{table}`
                    SET acategory = :audit_category, adescription = :audit_description
                    WHERE cfid = :cfid
                    """
                ),
                parameters=feedback_data
            )

            conn.commit()
            return True
    except Exception as e:
        print(f"Error updating feedback: {e}")
        return False

# Cloud Function handler
@functions_framework.http
def submit_audit_decision(request):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }

    if request.method == 'OPTIONS':
        response = make_response('', 204)
        response.headers.extend(headers)
        return response

    try:
        request_json = request.get_json()
        if not request_json:
            return make_response(jsonify({"error": "Invalid request"}), 400, headers)

        table = request_json.get("table")
        if table not in ["generative_first_reply", "accounts_and_billings", "skipped_or_spam"]:
            return make_response(jsonify({"error": "Invalid table name"}), 400, headers)

        feedback_data = {
            "cfid": request_json.get("cfid"),
            "audit_category": request_json.get("audit_category"),
            "audit_description": request_json.get("audit_description")
        }

        if not all(feedback_data.values()):
            return make_response(jsonify({"error": "Missing required fields"}), 400, headers)

        update_success = update_feedback_in_db(table, feedback_data)
        if not update_success:
            return make_response(jsonify({"error": "Database update failed"}), 500, headers)

        return make_response(jsonify({"status": "success", "message": "Feedback submitted successfully!"}), 200, headers)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500, headers)
