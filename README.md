# Vigía — Sistema de Bitácora Digital de Accesos

Proyecto organizado para desplegar el **backend en Render** y mantener el frontend y panel administrativo separados.

## Estructura

```text
vigia-sistema-bitacora/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── frontend/
│   └── index.html
├── admin/
│   └── index.html
├── render.yaml
├── .gitignore
└── README.md
```

## Backend en Render

El `render.yaml` ya está preparado para que Render use:

- **Root Directory:** `backend`
- **Build:** `pip install -r requirements.txt`
- **Start:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

En Render agrega como variables de entorno:

- `DATABASE_URL` — conexión PostgreSQL de producción.
- `ADMIN_API_KEY` — una clave privada para las rutas administrativas.

**No subas un archivo `.env` real al repositorio.** Usa `.env.example` como referencia.

## Frontend y administración

`frontend/index.html` es la pantalla de la caseta.

`admin/index.html` es el panel administrativo.

Ambos pueden alojarse como sitios estáticos y después apuntar a la URL pública del backend de Render.

## API

La documentación interactiva estará disponible en:

```text
https://TU-URL-DE-RENDER/docs
```
