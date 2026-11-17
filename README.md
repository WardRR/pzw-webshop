# Webshop API (Programiranje za web — 1. dio: backend)

REST API backend za internetsku trgovinu izrađen u **FastAPI-ju**, **SQLAlchemyju 2.0** (asinkroni PostgreSQL), **Alembicu**, **Pydanticu v2** i **pytestu**.

## Pokretanje na svježem klonu

### 1. Varijable okoline i baza podataka (PostgreSQL)
Iz korijena repozitorija kopirajte predložak konfiguracije i pokrenite PostgreSQL u Dockeru:

    cp .env.example .env
    docker compose up -d

### 2. Virtualno okruženje i ovisnosti
Uđite u mapu `api/`, stvorite virtualno okruženje i instalirajte pakete:

    cd api
    python -m venv .venv
    source .venv/Scripts/activate   # Windows (Git Bash)
    # source .venv/bin/activate     # Linux / macOS
    pip install -r requirements.txt

### 3. Migracije baze i početni podaci (idempotentni seed)
Primijenite Alembic migracije i popunite bazu početnim korisnicima i proizvodima:

    alembic upgrade head
    python -m app.seed

Početni računi nakon pokretanja `app.seed`:
- **Admin:** `admin@webshop.hr` / `admin123`
- **Kupac 1:** `kupac1@webshop.hr` / `kupac123`
- **Kupac 2:** `kupac2@webshop.hr` / `kupac123`

### 4. Pokretanje poslužitelja i Swagger dokumentacije

    uvicorn app.main:app --reload

Interaktivna OpenAPI/Swagger dokumentacija dostupna je na: `http://127.0.0.1:8000/docs`.

### 5. Pokretanje automatskih testova

    pytest

## Pregled glavnih krajnjih točaka (15 ruta)

- **Sustav:** `GET /health/live`, `GET /health/ready`
- **Autentikacija:** `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me`
- **Proizvodi:** `GET /products` (`search`, `in_stock`, `limit`, `offset`), `GET /products/{id}`, `POST /products` (admin), `PATCH /products/{id}` (admin), `DELETE /products/{id}` (admin — meko brisanje)
- **Narudžbe:** `POST /orders`, `GET /orders` (`limit`, `offset`), `GET /orders/{id}` (provjera vlasništva), `POST /orders/{id}/cancel` (rok 24h + povrat zalihe), `PATCH /orders/{id}/status` (admin)
