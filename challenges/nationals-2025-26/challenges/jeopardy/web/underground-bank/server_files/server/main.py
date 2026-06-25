from fastapi import FastAPI, Form, Depends, Header, HTTPException
import httpx
import jwt
import secrets
import os

app = FastAPI()
secret = secrets.token_hex(32)

@app.post("/register")
async def register(username: str = Form(...), password: str = Form(...)):
    async with httpx.AsyncClient() as client:
        response = await client.post("http://graphql:4000/graphql", json={
            "query": """
                mutation Register($username: String! = "%s", $password: String! = "%s") {
                    register(username: $username, password: $password)
                }
            """ % (username, password),
        })
        body = response.json()
        if body.get("data") and body["data"].get("register"):
            return {
                "success": True
            }
        return {"error": "Invalid credentials"}

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    async with httpx.AsyncClient() as client:
        response = await client.post("http://graphql:4000/graphql", json={
            "query": """
                query Login($username: String! = "%s", $password: String! = "%s") {
                    login(username: $username, password: $password)
                }
            """ % (username, password),
        })
        body = response.json()
        if body.get("data") and body["data"].get("login"):
            payload = {"username": username}
            if username == "admin":
                payload["flag"] = os.getenv("FLAG", "CyberSci{flag1}")
            return {
                "token": jwt.encode(payload, secret, algorithm="HS256")
            }
        return {"error": "Invalid credentials"}

# get token from authorization header
def get_user(authorization: str = Header()):
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        return jwt.decode(token, secret, algorithms=["HS256"])["username"]
    except:
        raise HTTPException(status_code=401, detail="Not authenticated")

@app.get("/requests")
async def get_requests(username: str = Depends(get_user)):
    async with httpx.AsyncClient() as client:
        response = await client.post("http://graphql:4000/graphql", json={
            "query": """
                query GetRequests {
                    requests {
                        id
                        amount
                    }
                }
            """
        }, headers={"x-request-user": username})
        body = response.json()
        return body

@app.post("/request-money")
async def request_money(request_from: str = Form(...), amount: float = Form(...), username: str = Depends(get_user)):
    async with httpx.AsyncClient() as client:
        response = await client.post("http://graphql:4000/graphql", json={
            "query": """
                mutation RequestMoney($from: String! = "%s", $amount: Float! = %d) {
                    requestMoney(from: $from, amount: $amount) {
                        id
                    }
                }
            """ % (request_from, amount),
        }, headers={"x-request-user": username})
        body = response.json()
        return body

@app.post("/accept-request")
async def accept_request(id: str = Form(...), username: str = Depends(get_user)):
    async with httpx.AsyncClient() as client:
        response = await client.post("http://graphql:4000/graphql", json={
            "query": """
                mutation AcceptRequest($id: String! = "%s") {
                    acceptRequest(id: $id)
                }
            """ % id,
        }, headers={"x-request-user": username})
        body = response.json()
        return body

@app.post("/set-webhook")
async def set_webhook(webhook: str = Form(...), username: str = Depends(get_user)):
    async with httpx.AsyncClient() as client:
        response = await client.post("http://graphql:4000/graphql", json={
            "query": """
                mutation SetWebhook($webhook: String! = "%s") {
                    setWebhook(webhook: $webhook)
                }
            """ % webhook,
        }, headers={"x-request-user": username})
        body = response.json()
        return body

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
