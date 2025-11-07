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

import logging
import logging.handlers as py_handlers
import os
import sys
from logging import Formatter, StreamHandler

LOG_FORMAT = '[%(asctime)s %(levelname)s] %(name)s:%(lineno)d - %(threadName)s - %(message)s'
LOG_FILEPATH = os.path.join(os.getcwd(), 'portal-metrics.log')

LOG_FILE_SIZE_MB = 300
LOG_FILE_SIZE_BYTES = LOG_FILE_SIZE_MB * 1000000
LOG_BACKUP_COUNT = 3


def get_file_handler(log_filepath, log_level):
    formatter = Formatter(LOG_FORMAT)
    f_handler = py_handlers.RotatingFileHandler(
        log_filepath, maxBytes=LOG_FILE_SIZE_BYTES, backupCount=LOG_BACKUP_COUNT
    )
    f_handler.setFormatter(formatter)
    f_handler.setLevel(log_level)
    return f_handler


def init_default_logger():
    formatter = Formatter(LOG_FORMAT)
    f_handler = get_file_handler(LOG_FILEPATH, logging.INFO)
    stream_handler = StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)
    logging.basicConfig(level=logging.DEBUG, handlers=[f_handler, stream_handler])
