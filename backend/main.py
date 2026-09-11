"""
Vigía · Bitácora Digital de Accesos — Fase 2 (Backend)

Mismos nombres de campo que el frontend de la Fase 1: placa, visitante,
tipo, destino — para que conectarlos sea un simple fetch().

Ejecutar en desarrollo:
    uvicorn main:app --reload
"""
import io
import os
from datetime import datetime

# import pandas as pd  # deshabilitado en Termux; export usa csv stdlib
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from database import Base, SessionLocal, engine, get_db
from models import Suscripcion, VehiculoAcceso
from schemas import EntradaCreate, SuscripcionOut, SuscripcionUpdate, VehiculoOut

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "cambia-esta-clave-en-produccion")

# Rutas que el kill switch NUNCA bloquea. Sin esto, un cliente suspendido
# no podría ni siquiera consultar su estado, y tú (el vendedor) no podrías
# reactivarlo llamando a tu propia API.
RUTAS_EXENTAS = {"/", "/docs", "/redoc", "/openapi.json", "/api/estado-suscripcion"}


def seed_suscripcion_inicial():
    """Un despliegue nuevo arranca 'active' (recién contratado), no bloqueado."""
    db = SessionLocal()
    try:
        if db.query(Suscripcion).first() is None:
            db.add(Suscripcion(cliente="Cliente Demo", status="active"))
            db.commit()
    finally:
        db.close()


seed_suscripcion_inicial()


# ---------------------------------------------------------------------------
# Kill switch — Control de Suspensión por falta de pago
# ---------------------------------------------------------------------------
class KillSwitchMiddleware(BaseHTTPMiddleware):
    """
    Antes de procesar cualquier request (salvo las exentas), revisa el
    status de la suscripción. Si no es 'active', corta con 402 Payment
    Required en vez de dejar pasar la petición.

    Esto lo controla el VENDEDOR del software, no el guardia ni el
    administrador del condominio — por eso /api/admin/* también queda
    exento (si no, ni tú podrías reactivar el servicio).
    """

    async def dispatch(self, request: Request, call_next):
        if request.url.path in RUTAS_EXENTAS or request.url.path.startswith("/api/admin"):
            return await call_next(request)

        db = SessionLocal()
        try:
            suscripcion = db.query(Suscripcion).order_by(Suscripcion.id.desc()).first()
        finally:
            db.close()

        if suscripcion is None or suscripcion.status != "active":
            return JSONResponse(
                status_code=402,
                content={
                    "error": "servicio_suspendido",
                    "mensaje": "El servicio está suspendido por falta de pago. Contacta a soporte para reactivar tu suscripción.",
                    "status": suscripcion.status if suscripcion else "sin_configurar",
                },
            )

        return await call_next(request)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="Vigía API", description="Bitácora digital de accesos", version="0.2.0")

# Orden importante: KillSwitch se agrega PRIMERO para que quede como capa
# interna, y CORS se agrega DESPUÉS para quedar como capa externa. Así, los
# headers CORS se aplican incluso a los 402 que corta el kill switch — si
# el orden fuera al revés, el navegador del frontend vería un error de CORS
# genérico en vez del mensaje real de "servicio suspendido".
app.add_middleware(KillSwitchMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en producción: restringe a tu dominio de Netlify/Vercel
    allow_methods=["*"],
    allow_headers=["*"],
)


def verificar_admin(x_admin_key: str = Header(default="")):
    if x_admin_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="No autorizado")


# ---------------------------------------------------------------------------
# Endpoints — Bitácora
# ---------------------------------------------------------------------------
@app.post("/api/entradas", response_model=VehiculoOut, status_code=201)
def registrar_entrada(datos: EntradaCreate, db: Session = Depends(get_db)):
    vehiculo = VehiculoAcceso(
        placa=datos.placa.strip().upper(),
        visitante=datos.visitante,
        tipo=datos.tipo.value,
        destino=datos.destino,
        hora_entrada=datetime.utcnow(),
    )
    db.add(vehiculo)
    db.commit()
    db.refresh(vehiculo)
    return vehiculo


@app.put("/api/salidas/{vehiculo_id}", response_model=VehiculoOut)
def registrar_salida(vehiculo_id: int, db: Session = Depends(get_db)):
    vehiculo = db.query(VehiculoAcceso).filter(VehiculoAcceso.id == vehiculo_id).first()
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    if vehiculo.hora_salida is not None:
        raise HTTPException(status_code=409, detail="Este vehículo ya registró su salida")

    vehiculo.hora_salida = datetime.utcnow()
    db.commit()
    db.refresh(vehiculo)
    return vehiculo


@app.get("/api/vehiculos-activos", response_model=list[VehiculoOut])
def vehiculos_activos(db: Session = Depends(get_db)):
    return (
        db.query(VehiculoAcceso)
        .filter(VehiculoAcceso.hora_salida.is_(None))
        .order_by(VehiculoAcceso.hora_entrada.desc())
        .all()
    )


@app.get("/api/historial", response_model=list[VehiculoOut])
def historial(db: Session = Depends(get_db)):
    """Historial completo (activos + con salida). Lo usa el panel de
    administración (Fase 3) para la tabla y las métricas; el filtrado por
    placa/visitante/fecha se hace en el propio frontend, en tiempo real."""
    return db.query(VehiculoAcceso).order_by(VehiculoAcceso.hora_entrada.desc()).all()


# ---------------------------------------------------------------------------
# Endpoint — Exportación a Excel
# ---------------------------------------------------------------------------
@app.get("/api/exportar")
def exportar_historial(
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    db: Session = Depends(get_db),
):
    import csv
    query = db.query(VehiculoAcceso)
    if fecha_desde:
        query = query.filter(VehiculoAcceso.hora_entrada >= datetime.fromisoformat(fecha_desde))
    if fecha_hasta:
        query = query.filter(VehiculoAcceso.hora_entrada <= datetime.fromisoformat(f"{fecha_hasta}T23:59:59"))
    vehiculos = query.order_by(VehiculoAcceso.hora_entrada.desc()).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Placa", "Visitante", "Tipo", "Destino", "Hora Entrada", "Hora Salida"])
    for v in vehiculos:
        writer.writerow([v.placa, v.visitante or "", v.tipo, v.destino or "", v.hora_entrada, v.hora_salida])
    buffer.seek(0)

    nombre_archivo = f"historial_accesos_{datetime.utcnow():%Y%m%d}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"},
    )


# ---------------------------------------------------------------------------
# Endpoints — Suscripción (uso del vendedor del software, no del cliente)
# ---------------------------------------------------------------------------
@app.get("/api/estado-suscripcion", response_model=SuscripcionOut)
def estado_suscripcion(db: Session = Depends(get_db)):
    suscripcion = db.query(Suscripcion).order_by(Suscripcion.id.desc()).first()
    if not suscripcion:
        return {"status": "sin_configurar", "cliente": None}
    return suscripcion


@app.put("/api/admin/suscripcion", dependencies=[Depends(verificar_admin)])
def actualizar_suscripcion(datos: SuscripcionUpdate, db: Session = Depends(get_db)):
    suscripcion = db.query(Suscripcion).order_by(Suscripcion.id.desc()).first()
    if not suscripcion:
        suscripcion = Suscripcion(status=datos.status.value)
        db.add(suscripcion)
    else:
        suscripcion.status = datos.status.value
    db.commit()
    db.refresh(suscripcion)
    return {"status": suscripcion.status}


@app.get("/")
def raiz():
    return {"servicio": "Vigía API", "estado": "ok"}
