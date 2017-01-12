# coding=utf-8

'''
由于Web框架使用了基于asyncio的aiohttp，这是基于协程的异步模型。
在协程中，不能调用普通的同步IO操作，因为所有用户都是由一个线程服务的，协程的执行速度必须非常快，才能处理大量用户的请求。
而耗时的IO操作不能在协程中以同步的方式调用，否则，等待一个IO操作时，系统无法响应任何其他用户。
这就是异步编程的一个原则：一旦决定使用异步，则系统每一层都必须是异步


'''

import logging;

import aiomysql
import asyncio

logging.basicConfig(level=logging.INFO)


@asyncio.coroutine
def create_pool(loop, **kwargs):
    logging.info("create database connect pool ...")
    global __pool
    __pool = yield from aiomysql.create_pool(
        host=kwargs.get('host', 'localhost'),
        port=kwargs.get('port', 3306),
        user=kwargs['user'],
        password=kwargs['password'],
        db=kwargs['db'],
        charset=kwargs.get('charset', 'utf8'),
        autocommit=kwargs.get('autocommit', True),
        maxsize=kwargs.get('maxsize', 10),
        minsize=kwargs.get('minsize', 1),
        loop=loop
    )
