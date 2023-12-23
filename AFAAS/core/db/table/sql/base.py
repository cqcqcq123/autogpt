from __future__ import annotations

import uuid

from AFAAS.interfaces.db_table import AbstractTable


class BaseSQLTable(AbstractTable):
    def __init__(self) -> None:
        raise NotImplementedError()

    def add(self, value: dict) -> uuid.UUID:
        id = uuid.uuid4()
        value["id"] = id
        self.memory.add(key=id, value=value, table_name=self.table_name)
        return id