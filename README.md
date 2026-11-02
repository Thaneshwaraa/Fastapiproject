# Car Management API

A small FastAPI app with an in-memory car database and a web UI.

## Run it

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

Then open the web UI:

- http://127.0.0.1:8000

You can also start it with `uvicorn main:app --reload`.

## Endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/cars` | List all cars |
| GET | `/cars/{car_id}` | Get one car |
| POST | `/cars` | Add a car |
| PUT | `/cars/{car_id}` | Replace a car |
| PUT | `/cars/{car_id}/update_year?year=2024` | Update a car's year |
| DELETE | `/cars/{car_id}` | Delete a car |

Data is stored in memory and resets when the server restarts.
