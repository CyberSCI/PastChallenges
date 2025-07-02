import base64
import json
import os
import urllib.parse
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

import jwt
import psycopg
import requests
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import PlainTextResponse
from fastapi.security import OAuth2PasswordBearer
from jwt.utils import base64url_decode
from pydantic import BaseModel
from psycopg.rows import dict_row

# Initialize FastAPI app
app = FastAPI(title="Key Management API")

# Get JWT settings from environment variables
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "a_default_secret_key_for_development_only")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Get the active key from environment variable
ACTIVE_KEY = os.getenv("ACTIVE_KEY", "default_key_value")

# OAuth2 scheme for token handling
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Setup postgres DB config
DB_PARAMS = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST"),
    "port": "5432",
}


# Models
class User(BaseModel):
    username: str


class TokenData(BaseModel):
    username: Optional[str] = None


class HealthResponse(BaseModel):
    message: str


class KeyResponse(BaseModel):
    key: str
    requesting_user: str


class ManagementKeyResponse(BaseModel):
    id: UUID
    public_key: str


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = psycopg.connect(**DB_PARAMS)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_db_cursor(commit=False):
    """Context manager for database cursors"""
    with get_db_connection() as conn:
        cursor = conn.cursor(row_factory=dict_row)
        try:
            yield cursor
            if commit:
                conn.commit()
        finally:
            cursor.close()


def decode_jwt(token):
    # Split the token into header, payload, and signature
    header_b64, payload_b64, signature = token.split(".")

    # Decode the base64url encoded payload
    # Add padding if needed
    payload_b64 += "=" * (4 - len(payload_b64) % 4) if len(payload_b64) % 4 else ""

    try:
        # Replace URL-safe characters and decode
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))
        return payload
    except Exception as e:
        print(f"Error decoding JWT: {e}")
        return None


# JWT verification function
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_jwt(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.PyJWTError as e:
        raise credentials_exception
    return token_data


# Helper function to create access tokens
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    # PyJWT in newer versions returns bytes, ensure we return a string
    if isinstance(encoded_jwt, bytes):
        return encoded_jwt.decode("utf-8")
    return encoded_jwt


# Health check route (unauthenticated)
@app.get("/health", response_model=HealthResponse)
async def health_check():
    return {"message": "ping"}


@app.get("/active-key", response_model=KeyResponse)
async def get_active_key(current_user: User = Depends(get_current_user)):
    key = "Active key is only visible to admin"
    if current_user.username == "admin":
        key = ACTIVE_KEY

    return {"key": key, "requesting_user": current_user.username}


@app.get("/token")
async def generate_token():
    username = "default"
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/fetch-url")
async def fetch_url(url: str):
    """
    Fetches content from the provided URL using GET method.
    Returns the content as plain text.
    TODO: Use this to grab: https://ntl2025vibemanagement.blob.core.windows.net/election-results/results.csv
    but for now we can just access that file with the managed identity from vpcadmin@10.0.2.22
    """
    try:
        # URL validation and sanitization
        decoded_url = urllib.parse.unquote(url)
        # Make the request
        response = requests.get(decoded_url, timeout=30)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses

        return PlainTextResponse(content=response.text)

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching URL: {str(e)}")


@app.get("/fetch-url-post")
async def fetch_url_post(url: str):
    """
    Fetches content from the provided URL using POST method.
    Returns the content as plain text.
    """
    try:
        # URL validation and sanitization
        decoded_url = urllib.parse.unquote(url)

        # Make the request
        response = requests.post(decoded_url, timeout=30)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses

        return PlainTextResponse(content=response.text)

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching URL: {str(e)}")


@app.get("/management-keys", response_model=List[ManagementKeyResponse])
async def get_management_keys(current_user: User = Depends(get_current_user)):
    """
    Retrieve all management keys (only ids and public keys)
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, public_key FROM management_keys")
            results = cursor.fetchall()

            # Convert to list of dicts (if not already in that format)
            keys = [dict(row) for row in results]

            return keys
    except psycopg.Error as e:
        # Log the actual error
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")


# Run with uvicorn if called directly
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
