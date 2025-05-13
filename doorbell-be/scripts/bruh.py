import jwt
import os
from dotenv import load_dotenv

def decode_token(token):
    load_dotenv()
    try:
        secret = os.environ.get('JWT_ACCESS_SECRET_KEY')
        # Just decode without verification
        payload = jwt.decode(token, options={"verify_signature": False})
        print(f"Decoded token: {payload}")

        # Try to verify with secret
        if secret:
            verified = jwt.decode(token, secret, algorithms=["HS256"])
            print("Token successfully verified!")
            user_id = payload.get("sub")
        return payload
    except Exception as e:
        print(f"Error: {str(e)}")
        return None


# Usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        decode_token(sys.argv[1])
    else:
        print("Usage: python script.py <token>")