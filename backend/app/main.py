import json
import os
import shutil
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

load_dotenv()

ADMIN_USER = os.getenv("ADMIN_USER", "admin@apartrincon.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "cambiar123")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "dev-token-change-me")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
DATABASE_PATH = os.getenv("DATABASE_PATH", "./apartrincon.db")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./static/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="ApartRincón API",
    description="API base para propiedades, galería y agenda privada de ApartRincón.",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PropertyBase(BaseModel):
    id: str
    name: str
    short_description: str = ""
    description: str = ""
    capacity: int = Field(default=1, ge=1)
    services: list[str] = []
    accessibility: list[str] = []
    images: list[str] = []
    active: bool = True


class BookingBase(BaseModel):
    property_id: str
    start_date: str
    end_date: str
    status: str = "reserved"
    guest_name: str = ""
    phone: str = ""
    notes: str = ""

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("La fecha debe usar formato YYYY-MM-DD") from exc
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        allowed = {"reserved", "blocked", "pending"}
        if value not in allowed:
            raise ValueError(f"Estado inválido. Usa uno de: {', '.join(sorted(allowed))}")
        return value


class BookingCreate(BookingBase):
    pass


class BookingUpdate(BaseModel):
    property_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None
    guest_name: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None



def get_db() -> sqlite3.Connection:
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection



def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    for key in ("services", "accessibility", "images"):
        if key in data:
            data[key] = json.loads(data[key] or "[]")
    if "active" in data:
        data["active"] = bool(data["active"])
    return data



def require_admin(authorization: str = Header(default="")) -> None:
    expected = f"Bearer {ADMIN_TOKEN}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="No autorizado")



def init_db() -> None:
    with get_db() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS properties (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                short_description TEXT DEFAULT '',
                description TEXT DEFAULT '',
                capacity INTEGER DEFAULT 1,
                services TEXT DEFAULT '[]',
                accessibility TEXT DEFAULT '[]',
                images TEXT DEFAULT '[]',
                active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id TEXT PRIMARY KEY,
                property_id TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'reserved',
                guest_name TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(property_id) REFERENCES properties(id)
            )
            """
        )

        count = db.execute("SELECT COUNT(*) AS total FROM properties").fetchone()["total"]
        if count == 0:
            now = datetime.utcnow().isoformat()
            seed_properties = [
                {
                    "id": "depto-1",
                    "name": "Departamento 1",
                    "short_description": "Departamento por temporada en Alta Gracia, preparado para una estadía cómoda, tranquila y funcional.",
                    "description": "Unidad equipada para huéspedes que buscan descanso, limpieza, seguridad y atención cercana. Ideal para consultar disponibilidad de forma directa por WhatsApp.",
                    "capacity": 4,
                    "services": ["WiFi", "Cocina equipada", "Ropa de cama", "Aire / calefacción", "TV"],
                    "accessibility": ["Ingreso cómodo", "Espacios funcionales"],
                    "images": [],
                    "active": 1,
                },
                {
                    "id": "depto-2",
                    "name": "Departamento 2",
                    "short_description": "Opción confortable para viajes, descanso o estadías temporarias cerca de Alta Gracia.",
                    "description": "Departamento equipado con servicios esenciales, distribución práctica y comunicación directa para coordinar fechas, consultas y condiciones de estadía.",
                    "capacity": 3,
                    "services": ["WiFi", "Cocina equipada", "Baño privado", "Ropa de cama", "Atención por WhatsApp"],
                    "accessibility": ["Circulación simple", "Ambientes prácticos"],
                    "images": [],
                    "active": 1,
                },
            ]

            for item in seed_properties:
                db.execute(
                    """
                    INSERT INTO properties (
                        id, name, short_description, description, capacity,
                        services, accessibility, images, active, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item["id"],
                        item["name"],
                        item["short_description"],
                        item["description"],
                        item["capacity"],
                        json.dumps(item["services"], ensure_ascii=False),
                        json.dumps(item["accessibility"], ensure_ascii=False),
                        json.dumps(item["images"], ensure_ascii=False),
                        item["active"],
                        now,
                        now,
                    ),
                )

        db.commit()


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    if payload.username != ADMIN_USER or payload.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return LoginResponse(access_token=ADMIN_TOKEN)


@app.get("/api/properties")
def list_public_properties() -> list[dict[str, Any]]:
    with get_db() as db:
        rows = db.execute("SELECT * FROM properties WHERE active = 1 ORDER BY created_at ASC").fetchall()
    return [row_to_dict(row) for row in rows]


@app.get("/api/admin/properties", dependencies=[Depends(require_admin)])
def list_admin_properties() -> list[dict[str, Any]]:
    with get_db() as db:
        rows = db.execute("SELECT * FROM properties ORDER BY created_at ASC").fetchall()
    return [row_to_dict(row) for row in rows]


@app.get("/api/properties/{property_id}")
def get_property(property_id: str) -> dict[str, Any]:
    with get_db() as db:
        row = db.execute("SELECT * FROM properties WHERE id = ? AND active = 1", (property_id,)).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")

    return row_to_dict(row)


@app.put("/api/admin/properties/{property_id}", dependencies=[Depends(require_admin)])
def update_property(property_id: str, payload: PropertyBase) -> dict[str, Any]:
    now = datetime.utcnow().isoformat()

    with get_db() as db:
        exists = db.execute("SELECT id FROM properties WHERE id = ?", (property_id,)).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Propiedad no encontrada")

        db.execute(
            """
            UPDATE properties
            SET name = ?, short_description = ?, description = ?, capacity = ?,
                services = ?, accessibility = ?, images = ?, active = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                payload.name,
                payload.short_description,
                payload.description,
                payload.capacity,
                json.dumps(payload.services, ensure_ascii=False),
                json.dumps(payload.accessibility, ensure_ascii=False),
                json.dumps(payload.images, ensure_ascii=False),
                1 if payload.active else 0,
                now,
                property_id,
            ),
        )
        db.commit()
        row = db.execute("SELECT * FROM properties WHERE id = ?", (property_id,)).fetchone()

    return row_to_dict(row)


@app.post("/api/admin/properties/{property_id}/images", dependencies=[Depends(require_admin)])
def upload_property_image(property_id: str, file: UploadFile = File(...)) -> dict[str, Any]:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos de imagen")

    suffix = Path(file.filename or "image").suffix.lower() or ".jpg"
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        raise HTTPException(status_code=400, detail="Formato no permitido. Usa JPG, PNG, WEBP o GIF")

    filename = f"{property_id}-{uuid.uuid4().hex}{suffix}"
    destination = UPLOAD_DIR / filename

    with get_db() as db:
        row = db.execute("SELECT * FROM properties WHERE id = ?", (property_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Propiedad no encontrada")

        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        data = row_to_dict(row)
        images = data.get("images") or []
        images.append(f"/uploads/{filename}")
        now = datetime.utcnow().isoformat()

        db.execute(
            "UPDATE properties SET images = ?, updated_at = ? WHERE id = ?",
            (json.dumps(images, ensure_ascii=False), now, property_id),
        )
        db.commit()
        updated = db.execute("SELECT * FROM properties WHERE id = ?", (property_id,)).fetchone()

    return row_to_dict(updated)



def validate_booking_dates(start_date: str, end_date: str) -> None:
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    if end <= start:
        raise HTTPException(status_code=400, detail="La fecha de salida debe ser posterior a la fecha de entrada")



def has_booking_conflict(
    db: sqlite3.Connection,
    property_id: str,
    start_date: str,
    end_date: str,
    ignore_booking_id: Optional[str] = None,
) -> bool:
    params: list[Any] = [property_id, end_date, start_date]
    query = """
        SELECT id FROM bookings
        WHERE property_id = ?
          AND status IN ('reserved', 'blocked')
          AND start_date < ?
          AND end_date > ?
    """

    if ignore_booking_id:
        query += " AND id != ?"
        params.append(ignore_booking_id)

    return db.execute(query, tuple(params)).fetchone() is not None


@app.get("/api/admin/bookings", dependencies=[Depends(require_admin)])
def list_admin_bookings() -> list[dict[str, Any]]:
    with get_db() as db:
        rows = db.execute("SELECT * FROM bookings ORDER BY start_date ASC").fetchall()
    return [dict(row) for row in rows]


@app.post("/api/admin/bookings", dependencies=[Depends(require_admin)])
def create_booking(payload: BookingCreate) -> dict[str, Any]:
    validate_booking_dates(payload.start_date, payload.end_date)

    now = datetime.utcnow().isoformat()
    booking_id = str(uuid.uuid4())

    with get_db() as db:
        property_exists = db.execute("SELECT id FROM properties WHERE id = ?", (payload.property_id,)).fetchone()
        if not property_exists:
            raise HTTPException(status_code=404, detail="Propiedad no encontrada")

        if payload.status in {"reserved", "blocked"} and has_booking_conflict(
            db,
            payload.property_id,
            payload.start_date,
            payload.end_date,
        ):
            raise HTTPException(status_code=409, detail="La propiedad ya tiene una reserva o bloqueo en esas fechas")

        db.execute(
            """
            INSERT INTO bookings (
                id, property_id, start_date, end_date, status,
                guest_name, phone, notes, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                booking_id,
                payload.property_id,
                payload.start_date,
                payload.end_date,
                payload.status,
                payload.guest_name,
                payload.phone,
                payload.notes,
                now,
                now,
            ),
        )
        db.commit()
        row = db.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()

    return dict(row)


@app.patch("/api/admin/bookings/{booking_id}", dependencies=[Depends(require_admin)])
def update_booking(booking_id: str, payload: BookingUpdate) -> dict[str, Any]:
    with get_db() as db:
        current = db.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")

        data = dict(current)
        updates = payload.model_dump(exclude_unset=True)
        data.update(updates)

        validate_booking_dates(data["start_date"], data["end_date"])

        if data["status"] in {"reserved", "blocked"} and has_booking_conflict(
            db,
            data["property_id"],
            data["start_date"],
            data["end_date"],
            ignore_booking_id=booking_id,
        ):
            raise HTTPException(status_code=409, detail="La propiedad ya tiene una reserva o bloqueo en esas fechas")

        now = datetime.utcnow().isoformat()
        db.execute(
            """
            UPDATE bookings
            SET property_id = ?, start_date = ?, end_date = ?, status = ?,
                guest_name = ?, phone = ?, notes = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                data["property_id"],
                data["start_date"],
                data["end_date"],
                data["status"],
                data["guest_name"],
                data["phone"],
                data["notes"],
                now,
                booking_id,
            ),
        )
        db.commit()
        row = db.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()

    return dict(row)


@app.delete("/api/admin/bookings/{booking_id}", dependencies=[Depends(require_admin)])
def delete_booking(booking_id: str) -> dict[str, str]:
    with get_db() as db:
        exists = db.execute("SELECT id FROM bookings WHERE id = ?", (booking_id,)).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")

        db.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        db.commit()

    return {"status": "deleted"}
