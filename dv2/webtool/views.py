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

from .models import Schema, Table, Column


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
    def table_names(self, request, pk=None):
        """
        Returns a list of all the table names that the schema owns.
        """
        schema = self.get_object()
        tables = schema.tables.all()
        return Response([table.name for table in tables])


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


def tables(request):
    context = {}
    return render(request, 'webtool/tables.html', context)


@api_view(['POST'])
def connect(request):
    """
    Connect to a source OLTP system
    """
    try:
        schemaManager.parse_schema(request.data)
    except Exception as e:
        logging.exception(e)
        return Response({"result": "ERROR", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return Response('{}', status=status.HTTP_200_OK)
