from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="Car Management API", description="API for managing car information", version="1.0.0", docs_url=None, redoc_url=None)

class car(BaseModel):
    id: int
    make: str
    model: str
    year: int

# In-memory storage (resets when the server restarts)
cars_db: dict[int, car] = {
    1: car(id=1, make="Toyota", model="Camry", year=2020),
    2: car(id=2, make="Honda", model="Civic", year=2019),
    3: car(id=3, make="Ford", model="Mustang", year=2021),
    4: car(id=4, make="Tesla", model="Model 3", year=2023),
    5: car(id=5, make="BMW", model="M3", year=2022),
    6: car(id=6, make="Mercedes-Benz", model="C-Class", year=2021),
    7: car(id=7, make="Audi", model="A4", year=2020),
    8: car(id=8, make="Chevrolet", model="Corvette", year=2023),
    9: car(id=9, make="Porsche", model="911 Carrera", year=2024),
    10: car(id=10, make="Hyundai", model="Tucson", year=2022),
    11: car(id=11, make="Kia", model="Seltos", year=2023),
    12: car(id=12, make="Mahindra", model="Thar", year=2024),
    13: car(id=13, make="Tata", model="Nexon", year=2023),
    14: car(id=14, make="Maruti Suzuki", model="Swift", year=2024),
    15: car(id=15, make="Nissan", model="GT-R", year=2019),
    16: car(id=16, make="Toyota", model="Fortuner", year=2022),
    17: car(id=17, make="Honda", model="City", year=2023),
    18: car(id=18, make="Jeep", model="Wrangler", year=2021),
    19: car(id=19, make="Volkswagen", model="Golf GTI", year=2020),
    20: car(id=20, make="Lamborghini", model="Huracán", year=2023),
}

def find_car(car_id: int) -> car:
    if car_id not in cars_db:
        raise HTTPException(status_code=404, detail=f"Car with id {car_id} not found")
    return cars_db[car_id]


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(Path(__file__).parent / "index.html")

@app.post("/cars", status_code=201)
def add_car(car: car):
    if car.id in cars_db:
        raise HTTPException(status_code=400, detail=f"Car with id {car.id} already exists")
    cars_db[car.id] = car
    return {"message": "Car added successfully", "car": car}

@app.get("/cars/{car_id}")
def get_car(car_id: int):
    return {"car": find_car(car_id)}

@app.put("/cars/{car_id}")
def update_car(car_id: int, car: car):
    find_car(car_id)
    if car.id != car_id:
        raise HTTPException(status_code=400, detail="Car id in body must match the URL")
    cars_db[car_id] = car
    return {"message": "Car updated successfully", "car": car}

@app.delete("/cars/{car_id}")
def delete_car(car_id: int):
    find_car(car_id)
    del cars_db[car_id]
    return {"message": "Car deleted successfully", "car_id": car_id}

@app.get("/cars")
def list_cars():
    return {"cars": list(cars_db.values())}

@app.put("/cars/{car_id}/update_year")
def update_car_year(car_id: int, year: int):
    find_car(car_id).year = year
    return {"message": "Car year updated successfully", "car_id": car_id, "new_year": year}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
