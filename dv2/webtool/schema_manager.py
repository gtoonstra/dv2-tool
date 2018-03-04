from sqlalchemy import create_engine
from sqlalchemy.engine import reflection
from webtool.schema import Schema


class SchemaManager(object):
    def __init__(self):
        self.schemas = {}
        self.output_dir = '/tmp/example'

    def _get_engine_url(self, connection_details):
        return '{engine}://{login}:{pass}@{host}:{port}/{schema}'.format(
            **connection_details)

    def count_tables(self):
        count = 0
        for schema_name, schema in self.schemas.items():
            count += schema.count_tables()
        return count

    def get_tables(self):
        tables = []
        for schema_name, schema in self.schemas.items():
            tables += schema.get_tables()
        return tables

    def parse_schema(self, login_details):
        engine = create_engine(self._get_engine_url(login_details))
        insp = reflection.Inspector.from_engine(engine)

        self.schemas = {}
        for schema_name in insp.get_schema_names():
            if schema_name == 'information_schema':
                continue
            self.schemas[schema_name] = Schema(schema_name)
            self.schemas[schema_name].parse(engine)

        for schema_name, schema in self.schemas.items():
            schema.resolve_foreign_keys(self.schemas)
            schema.guess_business_keys()
