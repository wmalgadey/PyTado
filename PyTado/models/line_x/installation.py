from PyTado.models.util import Base


class Installation(Base):
    """Installation model represents the installation object."""

    id: int
    name: str
