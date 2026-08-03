# ApartRincón - Base v3

Base de sitio web para **ApartRincón**, departamentos por temporada en Alta Gracia, Córdoba.

Esta versión prioriza el flujo comercial pedido por la administradora:

- El visitante **no ve la agenda ni la disponibilidad real**.
- El visitante consulta por WhatsApp.
- La administradora gestiona reservas, bloqueos y pendientes desde `/admin`.
- La agenda queda como calendario privado.
- Las reseñas funcionan como slider de 3 reseñas por página.
- El sitio público está separado en páginas: Inicio, Quiénes somos, Por qué elegirnos, Servicios, Propiedades, Galería y Contacto.
- La galería pública se alimenta con fotos cargadas desde el panel admin.

---

## Estructura

```txt
apart-rincon/
  frontend/      React + Vite
  backend/       FastAPI + SQLite
```

---

## Abrir en VS Code

Descomprime el ZIP y abre el workspace:

```txt
apartrincon.code-workspace
```

---

## Levantar backend

Desde una terminal en la carpeta `backend`:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --reload
```

Backend:

```txt
http://127.0.0.1:8000
```

Documentación API:

```txt
http://127.0.0.1:8000/docs
```

Recomendación: si aparece error con `pydantic-core`, usa Python 3.11 o 3.12 para el entorno virtual.

---

## Levantar frontend

Desde otra terminal en la carpeta `frontend`:

```powershell
npm install
copy .env.example .env
npm run dev
```

Frontend:

```txt
http://localhost:5173
```

Panel admin:

```txt
http://localhost:5173/admin
```

Credenciales demo:

```txt
Usuario: admin@apartrincon.com
Contraseña: cambiar123
```

Cambia estas credenciales antes de publicar.

---

## Variables importantes

### backend/.env

```txt
ADMIN_USER=admin@apartrincon.com
ADMIN_PASSWORD=cambiar123
ADMIN_TOKEN=dev-token-change-me
FRONTEND_URL=http://localhost:5173
DATABASE_PATH=./apartrincon.db
UPLOAD_DIR=./static/uploads
```

### frontend/.env

```txt
VITE_API_URL=http://127.0.0.1:8000
VITE_WHATSAPP_NUMBER=543547456045
VITE_GOOGLE_MAPS_EMBED_URL=
VITE_GOOGLE_REVIEWS_URL=
VITE_INSTAGRAM_URL=
```

El número de WhatsApp debe confirmarse. Si no abre correctamente, probablemente haya que usar formato Argentina con `549`, por ejemplo:

```txt
5493547456045
```

---

## Flujo público

El visitante puede:

- Ver información general.
- Ver quiénes son.
- Leer por qué elegir ApartRincón.
- Revisar servicios.
- Ver las propiedades.
- Entrar a la galería.
- Consultar por WhatsApp.
- Ver ubicación y reseñas.

El visitante no puede:

- Ver agenda de reservas.
- Ver días libres u ocupados.
- Crear reservas desde la web.

---

## Flujo admin

Desde `/admin`, la administradora puede:

- Iniciar sesión.
- Ver calendario privado por propiedad.
- Crear reservas.
- Crear bloqueos.
- Marcar consultas pendientes.
- Eliminar reservas/bloqueos.
- Editar nombre, descripción, capacidad, servicios e imágenes de cada propiedad.
- Subir fotos desde el panel.

Estados de agenda:

```txt
Reservado: cliente confirmado.
Bloqueado: fecha no disponible por decisión interna.
Pendiente: consulta avanzada, pero no cerrada.
```

La fecha `end_date` representa la salida/check-out. Si una reserva va del 10 al 15, se marcan ocupadas las noches del 10 al 14 y el día 15 queda como salida.

---

## Galería

Las fotos pueden cargarse de dos formas:

1. Desde el panel admin, usando el botón **Subir foto a la galería**.
2. Pegando URLs o rutas separadas por coma en el campo de imágenes de cada propiedad.

Las fotos cargadas desde admin se guardan en:

```txt
backend/static/uploads
```

Y se publican automáticamente en la página:

```txt
/galeria
```

---

## Reseñas

La sección de reseñas tiene un slider:

- Muestra 3 reseñas.
- Avanza automáticamente cada 7 segundos.
- Tiene botones para avanzar/retroceder.
- Tiene indicadores inferiores.

Los textos actuales son de base. Conviene reemplazarlos después por reseñas originales en español.

---

## Pendientes finos

- Confirmar nombres reales de las dos propiedades.
- Confirmar capacidad exacta de cada una.
- Confirmar servicios reales.
- Confirmar número de WhatsApp correcto.
- Agregar link de Google Maps embebido.
- Agregar link de Google Reviews.
- Agregar link de Instagram.
- Reemplazar reseñas base por reseñas originales en español.
- Cargar fotos reales desde el admin.
- Cambiar credenciales admin antes de publicar.
