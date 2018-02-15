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

    def guess_business_keys(self):
        for column_name, column in self.columns.items():
            if column.primary_key:
                self.bk_columns.append(column)

    def get_column(self, column_name):
        return self.columns[column_name]

    def generate_hash(self, output_file, alias_char, hash_key):
        if len(self.bk_columns) > 1:
            output_file.write('    , CONCAT(\n')

        collen = len(self.bk_columns)
        if len(self.bk_columns) > 1:
            for idx, col in enumerate(self.bk_columns):
                if (idx+1) == collen:
                    output_file.write("        LTRIM(RTRIM(COALESCE(CAST({0}.{1} AS VARCHAR), '')))\n".format(
                        alias_char, 
                        col.name))
                else:
                    output_file.write("        LTRIM(RTRIM(COALESCE(CAST({0}.{1} AS VARCHAR), ''))), ';',\n".format(
                        alias_char, 
                        col.name))
        else:
            col = self.bk_columns[0]
            output_file.write("    , LTRIM(RTRIM(COALESCE(CAST({0}.{1} AS VARCHAR), ''))) as {2}\n".format(
                alias_char, 
                col.name,
                hash_key))

        if len(self.bk_columns) > 1:
            output_file.write('      ) as hash_key_{0}\n'.format(self.name))

    def generate_select(self, output_file):
        alias_char = 'a'
        last_alias_char = alias_char
        with open(output_file, 'w') as f:
            f.write('SELECT\n')

            for column_name, column in self.columns.items():
                column.generate_select(f, alias_char)

            self.generate_hash(f, alias_char, 'hkey_{0}'.format(self.name))

            for constraint_name, key in self.foreign_keys.items():
                last_alias_char = chr(ord(last_alias_char) + 1)
                key.alias = last_alias_char

                tab = self.schema.get_table(key.tgt_table)
                hash_key = self.hash_keys[constraint_name]
                tab.generate_hash(f, key.alias, hash_key)

            f.write('FROM {0}.{1} {2}\n'.format(self.schema.name, self.name, alias_char))

            for constraint_name, key in self.foreign_keys.items():
                f.write('INNER JOIN {0}.{1} {2} ON '.format(
                    key.tgt_schema,
                    key.tgt_table,
                    key.alias))

                first = True
                for src_col, tgt_col in zip(key.src_columns, key.tgt_columns):
                    if first:
                        f.write('{0}.{1} = {2}.{3} '.format(
                            alias_char,
                            src_col,
                            key.alias,
                            tgt_col))
                    else:
                        f.write('AND {0}.{1} = {2}.{3} '.format(
                            alias_char,
                            src_col,
                            key.alias,
                            tgt_col))
                    first = False

                f.write('\n')

    def generate_select_foreign_keys(self, output_file, last_alias_char):
        new_alias_char = last_alias_char
        if self.has_foreign_key():
            # go to next letter
            new_alias_char = chr(ord(last_alias_char) + 1)
            self.foreign_alias = new_alias_char
            self.foreign_key.table.generate_hash(output_file, new_alias_char)

        return new_alias_char
