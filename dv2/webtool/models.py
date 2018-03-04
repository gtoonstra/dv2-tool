from django.db import models


class Schema(models.Model):
    name = models.CharField(max_length=200, primary_key=True)


class Table(models.Model):
    name = models.CharField(max_length=200, primary_key=True)
    schema = models.ForeignKey(Schema, related_name='tables', on_delete=models.CASCADE)
    target_schema = models.CharField(max_length=200)
    target_table = models.CharField(max_length=200)
    alias = models.CharField(max_length=200)


class Column(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    nullable = models.BooleanField(default=True)
    primary_key = models.BooleanField(default=True)
    alias = models.CharField(max_length=200)


class ForeignKey(models.Model):
    src_col = models.ForeignKey(Column, on_delete=models.PROTECT, related_name='src_col')
    tgt_col = models.ForeignKey(Column, on_delete=models.PROTECT, related_name='tgt_col')
