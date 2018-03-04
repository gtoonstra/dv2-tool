from django.db import models


class Schema(models.Model):
    name = models.CharField(max_length=200, primary_key=True)


class Table(models.Model):
    name = models.CharField(max_length=200)
    schema = models.ForeignKey(Schema, related_name='tables', on_delete=models.CASCADE)


class Column(models.Model):
    name = models.CharField(max_length=200)
    table = models.ForeignKey(Table, related_name='columns', on_delete=models.CASCADE)
    nullable = models.BooleanField(default=True)
    primary_key = models.BooleanField(default=True)
    alias = models.CharField(max_length=200)


class ForeignKey(models.Model):
    src_col = models.ForeignKey(Column, on_delete=models.PROTECT, related_name='src_col')
    tgt_col = models.ForeignKey(Column, on_delete=models.PROTECT, related_name='tgt_col')
