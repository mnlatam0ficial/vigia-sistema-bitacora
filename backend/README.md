# Vigía API — Backend (Fase 2)

Backend en FastAPI para la bitácora digital de accesos. Usa los mismos
nombres de campo que el frontend de la Fase 1: `placa`, `visitante`,
`tipo`, `destino`.

## 1. Instalación

```bash
cd backend
python -m venv venv
source venv/bin/activate      # En Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Por defecto usa SQLite (`bitacora.db`), así que no necesitas tocar el `.env`
para probar en local.

## 2. Ejecutar en desarrollo

```bash
uvicorn main:app --reload
```

- API: http://localhost:8000
- Documentación interactiva (Swagger): http://localhost:8000/docs

Las tablas se crean automáticamente al arrancar, y la suscripción queda en
`active` por defecto (para que un despliegue nuevo no arranque bloqueado).

## 3. Endpoints

| Método | Ruta                     | Descripción                                       |
|--------|--------------------------|----------------------------------------------------|
| POST   | `/api/entradas`          | Registra la entrada de un vehículo                  |
| PUT    | `/api/salidas/{id}`      | Registra la salida de un vehículo activo            |
| GET    | `/api/vehiculos-activos` | Lista los vehículos que aún no han salido           |
| GET    | `/api/exportar`          | Descarga el historial completo en Excel (.xlsx)     |
| GET    | `/api/estado-suscripcion`| Consulta el status de la suscripción                |
| PUT    | `/api/admin/suscripcion` | 🔒 Cambia el status (`active` / `overdue`)          |

### Probar con curl

```bash
# Registrar una entrada
curl -X POST http://localhost:8000/api/entradas \
  -H "Content-Type: application/json" \
  -d '{"placa":"ABC-123","visitante":"Juan Pérez","tipo":"Visita","destino":"Casa 24"}'

# Ver vehículos activos
curl http://localhost:8000/api/vehiculos-activos

# Registrar la salida (usa el id que devolvió el POST anterior)
curl -X PUT http://localhost:8000/api/salidas/1

# Descargar el Excel
curl -o historial.xlsx http://localhost:8000/api/exportar
```

## 4. Kill switch (control de suspensión)

Si el status de la suscripción no es `active`, **toda** la API responde
`402 Payment Required` — excepto `/`, `/docs`, `/api/estado-suscripcion` y
`/api/admin/*`, para que siempre puedas consultar o reactivar el servicio.

Este endpoint lo usas tú (el vendedor), no el cliente final — protégelo
cambiando `ADMIN_API_KEY` en tu `.env` antes de desplegar.

```bash
# Simular una suspensión por falta de pago
curl -X PUT http://localhost:8000/api/admin/suscripcion \
  -H "X-Admin-Key: cambia-esta-clave-en-produccion" \
  -H "Content-Type: application/json" \
  -d '{"status": "overdue"}'

# Reactivar
curl -X PUT http://localhost:8000/api/admin/suscripcion \
  -H "X-Admin-Key: cambia-esta-clave-en-produccion" \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'
```

## 5. Conectar a Supabase (Postgres) en producción

1. En tu proyecto de Supabase: **Project Settings → Database → Connection string** (modo URI).
2. Pega esa URL en `DATABASE_URL` dentro de `.env` (o como variable de entorno en tu hosting: Render, Railway, Fly.io, etc.).
3. `psycopg2-binary` ya está en `requirements.txt`, así que no necesitas nada más.
4. Corre la app normalmente — las tablas se crean solas al iniciar.

## 6. Conectar con el frontend (Fase 1)

En `index.html`, donde dice `// TODO (Fase 2)`, reemplaza esos comentarios
por llamadas `fetch()` a esta API (`http://localhost:8000` en desarrollo,
o la URL donde despliegues el backend en producción).
