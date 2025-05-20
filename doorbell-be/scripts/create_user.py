import asyncio
import os

import asyncpg
import bcrypt
import getpass

from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

async def create_user():
    email = input("Enter email: ")
    username = input("Enter username: ")
    password = getpass.getpass("Enter password: ")
    confirm = getpass.getpass("Re-enter password: ")

    if password != confirm:
        raise Exception("Passwords dont match")

    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    current_time = datetime.now()

    env = os.environ.get('ENV', 'DEV').upper()
    connection_string = os.environ[f'DB_CONNECTION_STRING_{env}']

    conn = await asyncpg.connect(connection_string)

    try:
        user_id = await conn.fetchval('''
            INSERT INTO users(
                email, 
                username, 
                password,
                created_at,
                modified_at
            ) VALUES($1, $2, $3, $4, $5)
            RETURNING id
        ''',
            email,
            username,
            hashed_password,
            current_time,
            current_time
        )

        print(f"User created successfully with ID: {user_id}")

    except asyncpg.UniqueViolationError as e:
        print(f"Error: A user with that email or username already exists: {e}")
    except Exception as e:
        print(f"Error creating user: {e}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(create_user())