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

## Login (JWT)

Anyone can view cars, but adding, editing and deleting need a login.

- Local demo login: username `admin`, password `admin123`
- Change them with the `DEMO_USERNAME` and `DEMO_PASSWORD` environment variables
- Set `SECRET_KEY` to a long random string in production (it signs the tokens)

`POST /login` returns a token that lasts 60 minutes. Send it on protected requests as
`Authorization: Bearer <token>`.

## Endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| POST | `/login` | Get a JWT token |
| GET | `/me` | Current user (login required) |
| GET | `/cars` | List all cars |
| GET | `/cars/{car_id}` | Get one car |
| POST | `/cars` | Add a car (login required) |
| PUT | `/cars/{car_id}` | Replace a car (login required) |
| PUT | `/cars/{car_id}/update_year?year=2024` | Update a car's year (login required) |
| DELETE | `/cars/{car_id}` | Delete a car (login required) |

Data is stored in memory and resets when the server restarts.

## Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Thaneshwaraa/Fastapiproject)

The `render.yaml` blueprint installs the requirements and starts the app with uvicorn.
