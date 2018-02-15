from sqlalchemy import create_engine
from sqlalchemy.engine import reflection
import json
from models import Table, Schema, Column


TYPE='postgres'
HOST='localhost'
PORT=5432
LOGIN='oltp_read'
PASS='oltp_read'
DB='adventureworks'


engine_url = '{0}://{1}:{2}@{3}:{4}/{5}'.format(
    TYPE,
    LOGIN,
    PASS,
    HOST,
    PORT,
    DB)


engine = create_engine(engine_url)
insp = reflection.Inspector.from_engine(engine)
output_dir = '/tmp/example'

schemas = {}
for schema_name in insp.get_schema_names():
    if schema_name == 'information_schema':
        continue
    schemas[schema_name] = Schema(schema_name)
    schemas[schema_name].parse(engine)

for schema_name, schema in schemas.items():
    schema.resolve_foreign_keys(schemas)
    schema.guess_business_keys()

for schema_name, schema in schemas.items():
    schema.generate_selects(output_dir)
