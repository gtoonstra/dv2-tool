from django.db import models
import collections
import logging


class Schema(models.Model):
    name = models.CharField(max_length=200, primary_key=True)


class Table(models.Model):
    name = models.CharField(max_length=200)
    schema = models.ForeignKey(Schema, related_name='tables', on_delete=models.CASCADE)

    def __init__(self, *args, **kwargs):
        super(Table, self).__init__(*args, **kwargs)
        self.bk_columns = []
        self.foreign_keys = {}
        self.hash_keys = {}

    def generate_select(self, output_file):
        alias_char = 'a'
        last_alias_char = alias_char
        with open(output_file, 'w') as f:
            f.write('SELECT\n')

            is_first = True
            for column in self.columns.all():
                if not column.select:
                    continue
                column.generate_select(f, alias_char, is_first)
                is_first = False
                if column.business_key:
                    self.bk_columns.append(column)

                fks = ForeignKey.objects.filter(src_col=column).all()
                for fk in fks:
                    fk = self.foreign_keys.get(fk.constraint_name, fk)
                    fk.add_column_mapping(fk.src_col, fk.tgt_col)
                    self.foreign_keys[fk.constraint_name] = fk

            tables = []
            for constraint_name, fk in self.foreign_keys.items():
                tables.append(fk.tgt_col.table.name)

            dups = [item for item, count in collections.Counter(tables).items() if count > 1]
            for constraint_name, fk in self.foreign_keys.items():
                if fk.tgt_col.table.name not in dups:
                    self.hash_keys[constraint_name] = 'hkey_{0}'.format(fk.tgt_col.table.name)
                else:
                    self.hash_keys[constraint_name] = 'hkey_{0}_{1}'.format(
                        fk.tgt_col.table.name, 
                        fk.src_col.name)

            self.generate_hash(f, alias_char, 'hkey_{0}'.format(self.name))

            for constraint_name, fk in self.foreign_keys.items():
                last_alias_char = chr(ord(last_alias_char) + 1)
                fk.alias = last_alias_char
                hash_key = self.hash_keys[constraint_name]
                tab = Table.objects.get(
                    schema=fk.tgt_col.table.schema.name,
                    name=fk.tgt_col.table.name)
                tab.generate_hash(f, fk.alias, hash_key)

            f.write('FROM {0}.{1} {2}\n'.format(self.schema.name, self.name, alias_char))

            for constraint_name, fk in self.foreign_keys.items():
                f.write('INNER JOIN {0}.{1} {2} ON '.format(
                    fk.tgt_col.table.schema.name,
                    fk.tgt_col.table.name,
                    fk.alias))

                first = True
                for src_col, tgt_col in zip(fk.src_cols, fk.tgt_cols):
                    if first:
                        f.write('{0}.{1} = {2}.{3} '.format(
                            alias_char,
                            src_col.name,
                            fk.alias,
                            tgt_col.name))
                    else:
                        f.write('AND {0}.{1} = {2}.{3} '.format(
                            alias_char,
                            src_col.name,
                            fk.alias,
                            tgt_col.name))
                    first = False

                f.write('\n')

    def generate_hash(self, output_file, alias_char, hash_key):
        if len(self.bk_columns) == 0:
            for column in self.columns.all():
                if not column.select:
                    continue
                if column.business_key:
                    self.bk_columns.append(column)

        if len(self.bk_columns) == 0:
            raise Exception("No business key defined on table {0}.{1}".format(
                self.schema.name,
                self.name))

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
            output_file.write('      ) as {0}\n'.format(hash_key))

    def generate_select_foreign_keys(self, output_file, last_alias_char):
        new_alias_char = last_alias_char
        if self.has_foreign_key():
            # go to next letter
            new_alias_char = chr(ord(last_alias_char) + 1)
            self.foreign_alias = new_alias_char
            self.foreign_key.table.generate_hash(output_file, new_alias_char)

        return new_alias_char


class Column(models.Model):
    name = models.CharField(max_length=200)
    table = models.ForeignKey(Table, related_name='columns', on_delete=models.CASCADE)
    nullable = models.BooleanField(default=True)
    primary_key = models.BooleanField(default=True)
    business_key = models.BooleanField(default=False)
    select = models.BooleanField(default=True)

    def generate_select(self, output_file, alias_char, is_first):
        self.alias = alias_char
        output_file.write('    {0} {1}.{2}\n'.format(
            ' ' if is_first else ',', 
            alias_char,
            self.name))        


class ForeignKey(models.Model):
    src_col = models.ForeignKey(Column, on_delete=models.PROTECT, related_name='src_col')
    tgt_col = models.ForeignKey(Column, on_delete=models.PROTECT, related_name='tgt_col')
    constraint_name = models.CharField(max_length=200)

    def __init__(self, *args, **kwargs):
        super(ForeignKey, self).__init__(*args, **kwargs)
        self.alias = 'xxxxx'
        self.src_cols = []
        self.tgt_cols = []

    def add_column_mapping(self, src_col, tgt_col):
        self.src_cols.append(src_col)
        self.tgt_cols.append(tgt_col)
