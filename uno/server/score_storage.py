# -*- coding: UTF-8 -*-
import logging
import asyncio
import asyncio_redis

logger = logging.getLogger(__name__)

WIN_SUFFIX = '_win_count'
LOSE_SUFFIX = '_lose_count'
REDIS_PARAMS = {'host': '127.0.0.1', 'port': 6379}

#TODO: permanent connection
async def get_user_score(username):
    connection = await asyncio_redis.Connection.create(**REDIS_PARAMS)
    win_count = await connection.get(username + WIN_SUFFIX)
    if win_count is None:
        win_count = 0
    else:
        win_count = int(win_count)
    lose_count = await connection.get(username + LOSE_SUFFIX)
    if lose_count is None:
        lose_count = 0
    else:
        lose_count = int(lose_count)
    if win_count + lose_count == 0:
        return 0
    else:
        return win_count / (win_count + lose_count)
    connection.close()
    return result


#TODO: permanent connection
async def record_user_score(username, result):
    connection = await asyncio_redis.Connection.create(**REDIS_PARAMS)
    if result:
        await connection.incrby(username + WIN_SUFFIX, 1)
    else:
        await connection.incrby(username + LOSE_SUFFIX, 1)
    print('write winrate', username, result)
    connection.close()
