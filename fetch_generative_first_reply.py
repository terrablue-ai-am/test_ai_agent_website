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

# Fetch list of pending cfids with optional filters
def get_filtered_cfid_list(ptitle_filter=None, rating_filter=None, start_date=None, end_date=None):
    pool = connect_with_connector()
    with pool.connect() as conn:
        conditions = ["(acategory IS NULL OR acategory = '' OR adescription IS NULL OR adescription = '')"]
        params = {}

        if ptitle_filter:
            ptitle_values = ptitle_filter.split(",")
            conditions.append("ptitle IN :ptitles")
            params["ptitles"] = tuple(ptitle_values)

        if rating_filter:
            rating_values = rating_filter.split(",")
            has_null = "Null" in rating_values
            clean_ratings = [r for r in rating_values if r != "Null"]

            if clean_ratings:
                conditions.append("rating IN :ratings")
                params["ratings"] = tuple(clean_ratings)

            if has_null:
                conditions.append("rating IS NULL")
        
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
                FROM `sav2_responses`.`generative_first_reply`
                WHERE {where_clause}
                ORDER BY dateupdated ASC;
                """
            ),
            params
        ).fetchall()

        return [dict(row._mapping) for row in rows] if rows else []

# Fetch full row by cfid
def get_ticket_details(cfid):
    pool = connect_with_connector()
    with pool.connect() as conn:
        row = conn.execute(
            sqlalchemy.text(
                """
                SELECT *
                FROM `sav2_responses`.`generative_first_reply`
                WHERE cfid = :cfid;
                """
            ),
            {"cfid": cfid}
        ).fetchone()

        return dict(row._mapping) if row else None

# Cloud Function entrypoint
@functions_framework.http
def fetch_gfr_tickets(request):
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
        rating_filter = request.args.get("rating")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")


        if cfid:
            data = get_ticket_details(cfid)
            if data:
                return jsonify({"status": "success", "data": data}), 200, headers
            else:
                return jsonify({"status": "not_found"}), 404, headers
        else:
            data = get_filtered_cfid_list(ptitle_filter, rating_filter, start_date, end_date)
            return jsonify({"status": "success", "data": data}), 200, headers

    except Exception as e:
        return jsonify({"error": str(e)}), 500, headers
