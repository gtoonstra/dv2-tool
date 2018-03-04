from .column import Column
from sqlalchemy.engine import reflection
import collections
from string import ascii_lowercase


class ForeignKey(object):
    """docstring for ForeignKey"""
    def __init__(self, src_schema, src_table, src_columns, tgt_schema, tgt_table, tgt_columns):
        super(ForeignKey, self).__init__()
        self.src_schema = src_schema
        self.src_table = src_table
        self.src_columns = src_columns
        self.tgt_schema = tgt_schema
        self.tgt_table = tgt_table
        self.tgt_columns = tgt_columns
        self.alias = 'xxxxxxxxx'


class Table(object):
    def __init__(self, name, schema):
        self.name = name
        self.schema = schema
        self.columns = collections.OrderedDict()
        self.bk_columns = []
        self.constraint_elements = {}
        self.foreign_keys = {}
        self.hash_keys = {}

    def parse(self, table_ref, engine):
        insp = reflection.Inspector.from_engine(engine)

        for constraint in table_ref.foreign_key_constraints:
            self.constraint_elements[constraint.name] = (constraint.columns, constraint.elements)

        d = {}
        for col_ref in table_ref.columns:
            column_name = col_ref.name
            col = Column(column_name, self)
            col.parse(engine, col_ref)
            d[column_name] = col

        self.columns = collections.OrderedDict(sorted(d.items(), key=lambda t: t[1].primary_key))
        for name, column in self.columns.items():
            column.is_first = True
            break

    def resolve_foreign_keys(self, schemas):
        for constraint_name, (columns, foreign_key_list) in self.constraint_elements.items():
            src_columns = []
            tgt_columns = []
            tgt_table = None
            tgt_schema = None
            src_table = None
            src_schema = None

            for column, foreign_key in zip(columns, foreign_key_list):
                src_columns.append(column.name)
                tgt_columns.append(foreign_key.column.name)
                src_schema = self.schema.name
                src_table = self.name
                tgt_schema = foreign_key.column.table.schema
                tgt_table = foreign_key.column.table.name

            key = ForeignKey(
                self.schema.name, 
                self.name, 
                src_columns,
                foreign_key.column.table.schema,
                foreign_key.column.table.name,
                tgt_columns)

            self.foreign_keys[constraint_name] = key

        tables = []
        for constraint_name, key in self.foreign_keys.items():
            tables.append(key.tgt_table)

        dups = [item for item, count in collections.Counter(tables).items() if count > 1]
        for constraint_name, key in self.foreign_keys.items():
            if key.tgt_table not in dups:
                self.hash_keys[constraint_name] = 'hkey_{0}'.format(key.tgt_table)
            else:
                self.hash_keys[constraint_name] = 'hkey_{0}_{1}'.format(key.tgt_table, key.src_columns[0])

    def get_foreign_keys(self):
        return self.foreign_keys

    def guess_business_keys(self):
        for column_name, column in self.columns.items():
            if column.primary_key:
                self.bk_columns.append(column)

    def get_column(self, column_name):
        return self.columns[column_name]

    def get_column_list(self):
        return list(self.columns.keys())

    def set_selected(self, col_list):
        self.selected = col_list

    def set_business_keys(self, col_list):
        self.bk_columns = []
        for col in col_list:
            self.bk_columns.append(self.get_column(col))
