from enum import StrEnum

from sqlalchemy import Enum
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def enum_column(enum_cls: type[StrEnum], constraint_name: str) -> Enum:
    """Колонка-перечисление как VARCHAR с проверкой значений на стороне базы.

    ``native_enum=False`` оставляет тип колонки строковым — так схема совпадает с исходной
    и добавление нового статуса не требует ``ALTER TYPE``. ``values_callable`` заставляет
    хранить именно значения (``uploaded``), а не имена членов (``UPLOADED``).
    """
    return Enum(
        enum_cls,
        native_enum=False,
        length=50,
        create_constraint=True,
        name=constraint_name,
        values_callable=lambda enum: [member.value for member in enum],
    )
