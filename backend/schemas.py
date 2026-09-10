from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TipoVisita(str, Enum):
    visita = "Visita"
    proveedor = "Proveedor"
    empleado = "Empleado"
    paqueteria = "Paquetería"


class EstadoSuscripcion(str, Enum):
    active = "active"
    overdue = "overdue"


class EntradaCreate(BaseModel):
    placa: str = Field(..., min_length=1, max_length=20, examples=["ABC-123"])
    visitante: Optional[str] = None
    tipo: TipoVisita
    destino: Optional[str] = None


class VehiculoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    placa: str
    visitante: Optional[str]
    tipo: str
    destino: Optional[str]
    hora_entrada: datetime
    hora_salida: Optional[datetime]


class SuscripcionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    cliente: Optional[str] = None


class SuscripcionUpdate(BaseModel):
    status: EstadoSuscripcion
