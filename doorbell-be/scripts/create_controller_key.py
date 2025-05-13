import os

import jwt
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()

    token = jwt.encode(
        {"id": "rpi"},
        key=os.getenv("JWT_ACCESS_SECRET_KEY"),
        algorithm=os.getenv("JWT_ALGORITHM")
    )

    print(token)
