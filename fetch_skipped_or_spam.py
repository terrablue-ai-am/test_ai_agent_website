import functions_framework
import pymysql
import sqlalchemy
import os
from flask import jsonify, request
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

# Fetch filtered cfid list
def get_filtered_sos_cfid_list(ptitle_filter=None, reason_filter=None):
    pool = connect_with_connector()
    with pool.connect() as conn:
        conditions = ["(acategory IS NULL OR acategory = '' OR adescription IS NULL OR adescription = '')"]
        params = {}

        if ptitle_filter:
            ptitle_values = ptitle_filter.split(",")
            conditions.append("ptitle IN :ptitles")
            params["ptitles"] = tuple(ptitle_values)

        if reason_filter:
            reason_values = reason_filter.split(",")
            conditions.append("reason IN :reasons")
            params["reasons"] = tuple(reason_values)

        where_clause = " AND ".join(f"({c})" for c in conditions)

        rows = conn.execute(
            sqlalchemy.text(
                f"""
                SELECT cfid
                FROM `sav2_responses`.`skipped_or_spam`
                WHERE {where_clause}
                ORDER BY dateupdated ASC;
                """
            ),
            params
        ).fetchall()

        return [dict(row._mapping) for row in rows] if rows else []

# Fetch full ticket details
def get_ticket_details(cfid):
    pool = connect_with_connector()
    with pool.connect() as conn:
        row = conn.execute(
            sqlalchemy.text(
                """
                SELECT *
                FROM `sav2_responses`.`skipped_or_spam`
                WHERE cfid = :cfid;
                """
            ),
            {"cfid": cfid}
        ).fetchone()

        return dict(row._mapping) if row else None

# Cloud Function entrypoint
@functions_framework.http
def fetch_skipped_or_spam_tickets(request):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }

    if request.method == 'OPTIONS':
        return ('', 204, headers)

    try:
        cfid = request.args.get("cfid")
        ptitle_filter = request.args.get("ptitle")
        reason_filter = request.args.get("reason")

        if cfid:
            data = get_ticket_details(cfid)
            if data:
                return jsonify({"status": "success", "data": data}), 200, headers
            else:
                return jsonify({"status": "not_found"}), 404, headers
        else:
            data = get_filtered_sos_cfid_list(ptitle_filter, reason_filter)
            return jsonify({"status": "success", "data": data}), 200, headers

    except Exception as e:
        return jsonify({"error": str(e)}), 500, headers
