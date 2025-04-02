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

# Function to fetch filtered cfids
def get_filtered_ab_cfid_list(ptitle_filter=None, cr_filter=None, srr_filter=None, start_date=None, end_date=None):
    pool = connect_with_connector()
    with pool.connect() as conn:
        conditions = ["(acategory IS NULL OR acategory = '' OR adescription IS NULL OR adescription = '')"]
        params = {}

        if ptitle_filter:
            ptitle_list = ptitle_filter.split(",")
            conditions.append("ptitle IN :ptitles")
            params["ptitles"] = tuple(ptitle_list)

        if cr_filter:
            cr_list = cr_filter.split(",")
            conditions.append("categorization_rating IN :cr")
            params["cr"] = tuple(cr_list)

        if srr_filter:
            srr_list = srr_filter.split(",")
            conditions.append("saved_reply_rating IN :srr")
            params["srr"] = tuple(srr_list)

        if start_date:
            conditions.append("DATE(dateupdated) >= :start_date")
            params["start_date"] = start_date

        if end_date:
            conditions.append("DATE(dateupdated) <= :end_date")
            params["end_date"] = end_date


        where_clause = " AND ".join(f"({c})" for c in conditions)

        rows = conn.execute(
            sqlalchemy.text(
                f"""
                SELECT cfid, comments
                FROM `sav2_responses`.`accounts_and_billings`
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
                FROM `sav2_responses`.`accounts_and_billings`
                WHERE cfid = :cfid;
                """
            ),
            {"cfid": cfid}
        ).fetchone()
        return dict(row._mapping) if row else None

# Cloud Function entrypoint
@functions_framework.http
def fetch_accounts_and_billings_tickets(request):
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
        cr_filter = request.args.get("categorization_rating")
        srr_filter = request.args.get("saved_reply_rating")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        if cfid:
            data = get_ticket_details(cfid)
            if data:
                return jsonify({"status": "success", "data": data}), 200, headers
            else:
                return jsonify({"status": "not_found"}), 404, headers
        else:
            data = get_filtered_ab_cfid_list(ptitle_filter, cr_filter, srr_filter, start_date, end_date)
            return jsonify({"status": "success", "data": data}), 200, headers

    except Exception as e:
        return jsonify({"error": str(e)}), 500, headers
