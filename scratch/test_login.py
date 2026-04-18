import requests
import os

def test_login():
    # Try the credentials from .env
    email = "admin@word2latex.local"
    password = "Admin@123456"
    
    # We need to know where the backend is running. 
    # Usually it's http://localhost:8000
    url = "http://localhost:8000/api/auth/login"
    
    payload = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")
    except Exception as e:
        print(f"Error connecting to backend: {e}")

if __name__ == "__main__":
    test_login()
