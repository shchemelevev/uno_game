# -*- coding: UTF-8 -*-
import logging
import asyncio
import asyncio_redis

logger = logging.getLogger(__name__)

#TODO: permanent connection
async def get_user_score(username):
    connection = await asyncio_redis.Connection.create(host='127.0.0.1', port=6379)
    result = await connection.get(username)
    if result is None:
        result = 0
    connection.close()
    return result

#TODO: permanent connection
async def record_user_score(username, score):
    connection = await asyncio_redis.Connection.create(host='127.0.0.1', port=6379)
    await connection.incrby(username, score)
    connection.close()
