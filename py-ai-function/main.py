from flask import make_response
import datetime

def ai_handler(request):
    if request.method == 'OPTIONS':
        response = make_response('')
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        return response

    # Handle POST request
    try:
        request_json = request.get_json(force=True)
        print("AI Servive was called. Received data:", request_json)

        response = make_response({
            "message": "AI service was called",
            "input": request_json,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'

        return response

    except Exception as e:
        print("Error:", e)
        return {"error": str(e)}, 400
