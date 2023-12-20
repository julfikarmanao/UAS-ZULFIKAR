from sqlalchemy import Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class   tb_printer(Base):
    __tablename__ = 'tb_printer'
    printer: Mapped[str] = mapped_column(primary_key=True)
    harga: Mapped[int] = mapped_column()
    jumlah_pin: Mapped[int] = mapped_column()
    resolusi: Mapped[int] = mapped_column()
    tegangan_listrik: Mapped[int] = mapped_column()
    berat: Mapped[int] = mapped_column()  
    
    def __repr__(self) -> str:
        return f"tb_printer(printer={self.tablet!r}, harga={self.harga!r})"
