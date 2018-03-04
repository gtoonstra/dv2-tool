from .models import Schema, Table, Column, ForeignKey
from rest_framework import serializers


class ColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Column
        fields = ('id', 'name', 'nullable', 'primary_key', 'business_key', 'select')


class TableSerializer(serializers.ModelSerializer):
    columns = ColumnSerializer(many=True, read_only=True)

    class Meta:
        model = Table
        fields = ('id', 'schema', 'name', 'columns')


class SchemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schema
        fields = ('name',)
