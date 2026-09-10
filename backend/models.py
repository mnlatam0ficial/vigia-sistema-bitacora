from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from database import Base


class VehiculoAcceso(Base):
    """Un registro de entrada/salida en la bitácora."""
    __tablename__ = "vehiculos_acceso"

    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String(20), nullable=False, index=True)
    visitante = Column(String(120), nullable=True)
    tipo = Column(String(30), nullable=False)  # Visita | Proveedor | Empleado | Paquetería
    destino = Column(String(80), nullable=True)
    hora_entrada = Column(DateTime, nullable=False, default=datetime.utcnow)
    hora_salida = Column(DateTime, nullable=True)


class Suscripcion(Base):
    """
    Estado de pago del cliente que usa este backend (el 'kill switch').
    Lo actualiza el VENDEDOR del software vía /api/admin/suscripcion,
    normalmente conectado a su propio sistema de cobros.
    """
    __tablename__ = "suscripcion"

    id = Column(Integer, primary_key=True, index=True)
    cliente = Column(String(120), nullable=False, default="Cliente")
    status = Column(String(20), nullable=False, default="active")  # 'active' | 'overdue'
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
