#   -*- coding: utf-8 -*-
#
#   This file is part of portal-metrics
#
#   Copyright (C) 2024 SKALE Labs
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os

from peewee import CharField, DateField, ForeignKeyField, IntegerField, Model
from playhouse.pool import PooledMySQLDatabase

db = PooledMySQLDatabase(
    os.getenv('MYSQL_DATABASE'),
    user=os.getenv('MYSQL_USER'),
    password=os.getenv('MYSQL_PASSWORD'),
    host=os.getenv('MYSQL_HOST'),
    port=int(os.getenv('MYSQL_PORT', 3306)),
    max_connections=8,
    stale_timeout=300,
)


class BaseModel(Model):
    class Meta:
        database = db


class Address(BaseModel):
    chain_name = CharField()
    address = CharField()
    app_name = CharField()


class TransactionCount(BaseModel):
    address = ForeignKeyField(Address, backref='transaction_counts')
    date = DateField()
    total_transactions = IntegerField()
    daily_transactions = IntegerField()

    class Meta:
        indexes = ((('address', 'date'), True),)
