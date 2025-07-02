from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
import uuid

API_DEV_TOKEN = "gAQru0xd0Xe1Xp2eve" # SECURITY 101 - A single hard-coded DEV TOKEN is simpler
SECRET_KEY = "2UmgQrZZxd0Xe1Xp2gGBCZev3"
APP_COMM_TOKEN = "3c34173f3e71353b71321015465561"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="identificar")

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

class Candidate:
    name: str
    id: str

    def __init__(self, name: str, id:str):
        self.name = name
        self.id = id

names_candidates = [
    "Esteban de Souza",
    "Arius Perez",
    "Raphael Velasquez",
    "Gen. Ramon Esperanza",
    "Joel Plata",
    "Sofia da Silva",
    "Ana Paula Espinoza",
    "Vera Gomes",
    "Xavier Gonzalez",
    "Pedro Galeano"
]

# Create list of Candidate objects with UUIDv4 ids
candidates = [Candidate(name, str(uuid.uuid4())) for name in names_candidates]

class UserInfo:
    postal_code: str
    year_of_birth: int
    social_security: str
    candidate_vote: str

    def __init__(self, postal_code: str, year_of_birth: int, social_security: str):
        self.postal_code = postal_code
        self.social_security = social_security
        self.year_of_birth = year_of_birth
        self.candidate_vote = ""

    def __eq__(self, other):
        if not isinstance(other, UserInfo):
            return NotImplemented
        return self.postal_code == other.postal_code and self.year_of_birth == other.postal_code and self.social_security == other.social_security
    
    def vote(self, candidate_id:str) -> None:
        self.candidate_vote = candidate_id

app = FastAPI(
    title="Fake Server",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

valid_users = {
    "jeanine_lopez" : "password"
}

user_validations = {
    "jeanine_lopez": True
}

user_infos = {
    "jeanine_lopez": UserInfo("AUT2111", 2000, "TT1214512131")
}

@app.post("/usarios")
def usarios(dev_token: str = Form(...)):
    if dev_token != API_DEV_TOKEN:
        raise HTTPException(status_code=401, detail="Acceso no autorizado")
    return valid_users

@app.post("/identificar")
async def identificar(username: str = Form(...), password: str = Form(...)):
    if valid_users.get(username) == password:
        access_token = create_access_token(
        data={"sub": username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        return {"token": access_token}
    raise HTTPException(status_code=401, detail="Acceso no autorizado")

@app.post("/restablecer-validacion")
async def restablecer(username: str = Form(...), dev_token: str = Form(..., example=API_DEV_TOKEN)):
    if dev_token != API_DEV_TOKEN:
        raise HTTPException(status_code=401, detail="Acceso no autorizado")
    if valid_users.get(username):
        valid_users[username] = False
        return {"message": "ok"}
    else:
        raise HTTPException(status_code=404, detail="No se ha encontrado al usuario")

@app.get("/candidatos")
def candidatos():
    return candidates

@app.post("/votar")
def votar(token: str = Form(...), candidate_id: str = Form(...), app_token: str = Form(...)):
    if app_token!=APP_COMM_TOKEN:
        raise HTTPException(status_code=401, detail="Acceso no autorizado - invalid special token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Acceso no autorizado")
        if not any(c.id == candidate_id for c in candidates):
            raise HTTPException(status_code=400, detail="El candidato no existe")
        if not valid_users.get(username):
            raise HTTPException(status_code=403, detail="El usuario aún no ha sido verificado")
        user_infos.get(username).vote(candidate_id)
        return {"success":True, "vote_confirmation_number": "VALVERDE_A4E5610B2AE", "flag":"FLAG-41237469ca5b5c4c2"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Acceso no autorizado3")

@app.post("/validar")
async def validar(username: str = Form(...), token: str = Depends(oauth2_scheme), social_security: str = Form(...), postal_code: str = Form(...), year_of_birth: int = Form(...)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Acceso no autorizado")
        if not validate(username, UserInfo(postal_code, year_of_birth,social_security)):
            raise HTTPException(status_code=422, detail="Los valores no coinciden con el contenido de la base de datos del estado de Valverde")
        user_validations[username] = True
        return {"success":True}
    except JWTError:
        raise HTTPException(status_code=401, detail="Acceso no autorizado")

@app.post("/registrar")
def registrar(username: str = Form(...), password: str = Form(...)):
    raise HTTPException(status_code=501, detail="Esta función aún no está implementada")

def validate(username: str, user_info: UserInfo) -> bool:
    info: UserInfo = user_infos.get(username)
    return info.postal_code == user_info.postal_code and info.social_security == user_info.social_security and info.year_of_birth == user_info.year_of_birth