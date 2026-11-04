import hmac
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import Integer, String, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

app = FastAPI(title="Car Management API", description="API for managing car information", version="1.0.0", docs_url=None, redoc_url=None)

# JWT settings (set these as environment variables when deploying)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-key-change-me-in-production")
ALGORITHM = "HS256"
TOKEN_MINUTES = 60
DEMO_USERNAME = os.getenv("DEMO_USERNAME", "admin")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "admin123")

# Google sign-in settings
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
# Comma-separated list of Google emails that may sign in, e.g. "you@gmail.com,friend@gmail.com"
ALLOWED_EMAILS = {e.strip().lower() for e in os.getenv("ALLOWED_EMAILS", "").split(",") if e.strip()}

bearer = HTTPBearer(auto_error=False)

class LoginRequest(BaseModel):
    username: str
    password: str

class GoogleLoginRequest(BaseModel):
    credential: str

def create_token(username: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_MINUTES)
    return jwt.encode({"sub": username, "exp": expires}, SECRET_KEY, algorithm=ALGORITHM)

def current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> str:
    unauthorized = HTTPException(status_code=401, detail="Please log in to make changes", headers={"WWW-Authenticate": "Bearer"})
    if creds is None:
        raise unauthorized
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired, please log in again", headers={"WWW-Authenticate": "Bearer"})
    except jwt.InvalidTokenError:
        raise unauthorized
    return payload["sub"]

class car(BaseModel):
    id: int
    make: str
    model: str
    year: int

# Database: PostgreSQL via DATABASE_URL, e.g. postgresql://postgres:password@localhost:5432/cars
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/cars")
# Use the psycopg 3 driver (Render gives URLs starting with postgres://)
DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1).replace("postgresql://", "postgresql+psycopg://", 1)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

class Base(DeclarativeBase):
    pass

class CarRow(Base):
    __tablename__ = "cars"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    make: Mapped[str] = mapped_column(String(100))
    model: Mapped[str] = mapped_column(String(100))
    year: Mapped[int] = mapped_column(Integer)

SEED_CARS = [
    ("Toyota", "Camry", 2020), ("Honda", "Civic", 2019), ("Ford", "Mustang", 2021),
    ("Tesla", "Model 3", 2023), ("BMW", "M3", 2022), ("Mercedes-Benz", "C-Class", 2021),
    ("Audi", "A4", 2020), ("Chevrolet", "Corvette", 2023), ("Porsche", "911 Carrera", 2024),
    ("Hyundai", "Tucson", 2022), ("Kia", "Seltos", 2023), ("Mahindra", "Thar", 2024),
    ("Tata", "Nexon", 2023), ("Maruti Suzuki", "Swift", 2024), ("Nissan", "GT-R", 2019),
    ("Toyota", "Fortuner", 2022), ("Honda", "City", 2023), ("Jeep", "Wrangler", 2021),
    ("Volkswagen", "Golf GTI", 2020), ("Lamborghini", "Huracán", 2023),
]

@app.on_event("startup")
def init_db():
    # Creates the table if missing and adds the sample cars to an empty table
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        if db.scalar(select(func.count()).select_from(CarRow)) == 0:
            db.add_all(CarRow(id=i, make=m, model=mo, year=y) for i, (m, mo, y) in enumerate(SEED_CARS, start=1))
            db.commit()

def get_db():
    with Session(engine) as db:
        yield db

def to_car(row: CarRow) -> car:
    return car(id=row.id, make=row.make, model=row.model, year=row.year)

def find_car(db: Session, car_id: int) -> CarRow:
    row = db.get(CarRow, car_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Car with id {car_id} not found")
    return row


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(Path(__file__).parent / "index.html")

@app.post("/login")
def login(body: LoginRequest):
    valid_user = hmac.compare_digest(body.username, DEMO_USERNAME)
    valid_password = hmac.compare_digest(body.password, DEMO_PASSWORD)
    if not (valid_user and valid_password):
        raise HTTPException(status_code=401, detail="Wrong username or password")
    return {"access_token": create_token(body.username), "token_type": "bearer", "username": body.username}

@app.get("/auth/config")
def auth_config():
    return {"google_client_id": GOOGLE_CLIENT_ID or None}

@app.post("/auth/google")
def google_login(body: GoogleLoginRequest):
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Google sign-in is not set up on this server")
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token

    try:
        # Checks Google's signature, the expiry, and that the token was issued for our client ID
        info = id_token.verify_oauth2_token(body.credential, google_requests.Request(), GOOGLE_CLIENT_ID)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google sign-in, please try again")
    email = (info.get("email") or "").lower()
    if not info.get("email_verified") or email not in ALLOWED_EMAILS:
        raise HTTPException(status_code=403, detail=f"{email or 'This account'} is not allowed to make changes")
    return {"access_token": create_token(email), "token_type": "bearer", "username": email}

@app.get("/me")
def me(user: str = Depends(current_user)):
    return {"username": user}

@app.post("/cars", status_code=201)
def add_car(car: car, user: str = Depends(current_user), db: Session = Depends(get_db)):
    if db.get(CarRow, car.id) is not None:
        raise HTTPException(status_code=400, detail=f"Car with id {car.id} already exists")
    db.add(CarRow(**car.model_dump()))
    db.commit()
    return {"message": "Car added successfully", "car": car}

@app.get("/cars/{car_id}")
def get_car(car_id: int, db: Session = Depends(get_db)):
    return {"car": to_car(find_car(db, car_id))}

@app.put("/cars/{car_id}")
def update_car(car_id: int, car: car, user: str = Depends(current_user), db: Session = Depends(get_db)):
    row = find_car(db, car_id)
    if car.id != car_id:
        raise HTTPException(status_code=400, detail="Car id in body must match the URL")
    row.make, row.model, row.year = car.make, car.model, car.year
    db.commit()
    return {"message": "Car updated successfully", "car": car}

@app.delete("/cars/{car_id}")
def delete_car(car_id: int, user: str = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(find_car(db, car_id))
    db.commit()
    return {"message": "Car deleted successfully", "car_id": car_id}

@app.get("/cars")
def list_cars(db: Session = Depends(get_db)):
    return {"cars": [to_car(r) for r in db.scalars(select(CarRow).order_by(CarRow.id))]}

@app.put("/cars/{car_id}/update_year")
def update_car_year(car_id: int, year: int, user: str = Depends(current_user), db: Session = Depends(get_db)):
    find_car(db, car_id).year = year
    db.commit()
    return {"message": "Car year updated successfully", "car_id": car_id, "new_year": year}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
