from .table import Table
from sqlalchemy import MetaData
import os
import logging


logger = logging.getLogger(__name__)


class Schema(object):
    def __init__(self, name):
        self.name = name
        self.tables = {}

    def parse(self, engine):
        meta = MetaData(bind=engine)
        meta.clear()
        meta.reflect(schema=self.name)

        for table_ref in meta.sorted_tables:
            if table_ref.schema != self.name:
                # This is a table imported through a foreign key
                continue
            table_name = table_ref.name
            self.tables[table_name] = Table(table_name, self)
            self.tables[table_name].parse(table_ref, engine)

    def resolve_foreign_keys(self, schemas):
        for table_name, table in self.tables.items():
            table.resolve_foreign_keys(schemas)

    def guess_business_keys(self):
        for table_name, table in self.tables.items():
            table.guess_business_keys()        

    def get_table(self, table_name):
        return self.tables[table_name]

    def count_tables(self):
        return len(self.tables)

    def get_tables(self):
        return list(self.tables.values())
