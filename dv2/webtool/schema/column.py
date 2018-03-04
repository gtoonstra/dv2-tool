

class Column(object):
    def __init__(self, name, table):
        self.name = name
        self.table = table
        self.nullable = False
        self.primary_key = False
        self.foreign_key_ref = None
        self.is_first = False
        self.foreign_key = None
        self.alias = ''

    def parse(self, engine, col_ref):
        self.nullable = col_ref.nullable
        self.primary_key = col_ref.primary_key
