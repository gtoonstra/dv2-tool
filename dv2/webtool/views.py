from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.decorators import detail_route
from rest_framework import status
from .serializers import SchemaSerializer
from .serializers import TableSerializer
from .serializers import ColumnSerializer
from .schema_manager import SchemaManager
import logging
import os

from .models import Schema, Table, Column, ForeignKey


logger = logging.getLogger(__name__)
schemaManager = SchemaManager()


def index(request):
    return render(request, 'webtool/index.html', {})


class SchemaViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Schema.objects.all()
    serializer_class = SchemaSerializer

    @detail_route()
    def tables(self, request, pk=None):
        """
        Returns a list of all the table names that the schema owns.
        """
        schema = self.get_object()
        tables = schema.tables.all().order_by('name')
        return Response([{"id": table.id, "name": table.name} for table in tables])

    @detail_route(methods=['post'])
    def generate(self, request, pk=None):
        schema = self.get_object()
        output_dir = request.data['output_dir']
        schema_output_dir = os.path.join(output_dir, schema.name)

        try:
            os.makedirs(schema_output_dir)
        except OSError:
            pass

        for table in schema.tables.all():
            file_name = os.path.join(schema_output_dir, "{0}.sql".format(table.name))
            table.generate_select(file_name)

        return Response('{}', status=status.HTTP_200_OK)


class TableViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Table.objects.all()
    serializer_class = TableSerializer


class ColumnViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Column.objects.all()
    serializer_class = ColumnSerializer

    def update(self, request, pk):
        instance = Column.objects.get(id=pk)
        instance.business_key = request.data.get('business_key', instance.business_key)
        instance.select = request.data.get('select', instance.select)
        instance.save()
        return Response('{}', status=status.HTTP_200_OK)

def parse(request):
    context = {}
    return render(request, 'webtool/parse.html', context)


@api_view(['POST'])
def connect(request):
    """
    Connect to a source OLTP system and parse the schema,
    then truncate schema with that name and reinsert.
    """
    try:
        schemaManager.parse_schema(request.data)
    except Exception as e:
        logging.exception(e)
        return Response({"result": "ERROR", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    schemas = schemaManager.get_schemas()
    for schema_name in schemas:
        schema = schemaManager.get_schema(schema_name)

        model_schema = None
        try:
            model_schema = Schema.objects.get(pk=schema_name)
        except Schema.DoesNotExist:
            model_schema = Schema.objects.create(name=schema_name)
        model_schema.save()
        model_schema.refresh_from_db()

        table_list = schema.get_tables()
        for table in table_list:
            model_table = None
            try:
                model_table = Table.objects.get(name=table.name, schema=model_schema)
            except Table.DoesNotExist:
                model_table = Table.objects.create(name=table.name, schema=model_schema)
            model_table.save()
            model_table.refresh_from_db()

            column_list = table.get_column_list()
            for column_name in column_list:
                column = table.get_column(column_name)
                model_column = None
                try:
                    model_column = Column.objects.get(name=column.name, table=model_table)
                except Column.DoesNotExist:
                    model_column = Column.objects.create(name=column.name, table=model_table)
                model_column.nullable = column.nullable
                model_column.primary_key = column.primary_key
                model_column.save()

    for schema_name in schemas:
        schema = schemaManager.get_schema(schema_name)
        model_schema = Schema.objects.get(pk=schema_name)
        table_list = schema.get_tables()
        for table in table_list:
            model_table = Table.objects.get(name=table.name, schema=model_schema)
            foreign_keys = table.get_foreign_keys()

            for constraint_name, fkey in foreign_keys.items():
                src_schema = Schema.objects.get(pk=fkey.src_schema)
                tgt_schema = Schema.objects.get(pk=fkey.tgt_schema)
                src_table = Table.objects.get(name=fkey.src_table, schema=src_schema)
                tgt_table = Table.objects.get(name=fkey.tgt_table, schema=tgt_schema)
                for src_col_name, tgt_col_name in zip(fkey.src_columns, fkey.tgt_columns):
                    src_col = Column.objects.get(name=src_col_name, table=src_table)
                    tgt_col = Column.objects.get(name=tgt_col_name, table=tgt_table)

                    fk = None
                    try:
                        fk = ForeignKey.objects.get(src_col=src_col, tgt_col=tgt_col)
                    except ForeignKey.DoesNotExist:
                        fk = ForeignKey.objects.create(src_col=src_col, tgt_col=tgt_col)

                    fk.constraint_name = constraint_name
                    fk.save()

    return Response('{}', status=status.HTTP_200_OK)


def generate(request):
    context = {}
    return render(request, 'webtool/generate.html', context)
