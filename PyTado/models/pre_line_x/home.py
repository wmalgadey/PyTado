from typing import List
from pydantic import TypeAdapter
from PyTado.models.util import Base

class HeatingCircuit(Base):
    number: int
    driverSerialNo: str
    driverShortSerialNo: str

HeatingCircuits = TypeAdapter(List[HeatingCircuit])