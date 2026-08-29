import jwt
import hashlib
from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

SECRET_KEY = "super_secret_jwt_key_12345"
API_KEY = "sk-prod-a1b2c3d4e5f6g7h8i9j0"
DATABASE_PASSWORD = "admin123!"

def get_db_connection():
    import psycopg2
    return psycopg2.connect(
        host="localhost",
        database="myapp",
        user="admin",
        password=DATABASE_PASSWORD
    )

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    hashed = hashlib.sha256(password.encode()).hexdigest()

    token = jwt.encode(
        {'user': username, 'exp': datetime.utcnow() + timedelta(hours=24)},
        SECRET_KEY,
        algorithm='HS256'
    )

    return jsonify({'token': token})

@app.route('/api/data')
def get_data():
    auth_header = request.headers.get('Authorization', '')

    if auth_header != f"Bearer {API_KEY}":
        return jsonify({'error': 'Unauthorized'}), 401

    return jsonify({'data': 'sensitive information'})

@app.route('/verify')
def verify_token():
    token = request.args.get('token', '')

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return jsonify({'valid': True, 'user': payload['user']})
    except jwt.InvalidTokenError:
        return jsonify({'valid': False}), 401

if __name__ == '__main__':
    app.run(debug=True)
