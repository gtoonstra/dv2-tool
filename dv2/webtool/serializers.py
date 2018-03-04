from .models import Schema, Table, Column
from rest_framework import serializers


class ColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Column
        fields = ('name', 'nullable', 'primary_key', 'alias')


class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ('schema', 'name', 'target_schema', 'target_table', 'alias')


class SchemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schema
        fields = ('name',)
