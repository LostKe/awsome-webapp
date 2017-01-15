# coding=utf-8

'''
由于Web框架使用了基于asyncio的aiohttp，这是基于协程的异步模型。
在协程中，不能调用普通的同步IO操作，因为所有用户都是由一个线程服务的，协程的执行速度必须非常快，才能处理大量用户的请求。
而耗时的IO操作不能在协程中以同步的方式调用，否则，等待一个IO操作时，系统无法响应任何其他用户。
这就是异步编程的一个原则：一旦决定使用异步，则系统每一层都必须是异步


aiomysql为MySQL数据库提供了异步IO的驱动。


'''

import logging;

import aiomysql
import asyncio

logging.basicConfig(level=logging.INFO)


def log(sql, args):
    logging.info("SQL:%s" % sql, args)


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


"""
sql:sql 语句
args:sql 参数
size:需要查询结果的数量
"""


@asyncio.coroutine
def select(sql, args, size=None):
    log(sql, args)
    global __pool
    with(yield from __pool) as conn:
        cur = yield from conn.cursor(aiomysql.DictCursor)
        yield from cur.execute(sql.replace('?', '%'), args or ())
        if size:
            rs = yield from cur.fetchmany(size)
        else:
            rs = yield from cur.fetchall()
        yield from cur.close()
        logging.info('rows return:%s' % len(rs))
        return rs


"""
通用的 delete update insert
"""


@asyncio.coroutine
def execute(sql, args):
    log(sql, args)
    global __pool
    with(yield from __pool) as conn:
        try:
            cur = yield from conn.cursor()
            yield from cur.execute(sql.replace('?', '%'), args)
            affect_count = cur.rowcount
            yield from cur.close()
        except BaseException as e:
            print(e)
            raise
        return affect_count


class Filed(object):
    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default


class StringFiled(Filed):
    def __init__(self, name=None, primary_key=False, default=None, column_type='varchar(100)'):
        super().__init__(self, name, column_type, primary_key, default)


class IntegerFiled(Filed):
    def __init__(self, name=None, primary_key=False, default=None):
        super().__init__(self, name, 'int', primary_key, default)


class BooleanFiled(Filed):
    def __init__(self, name=None, default=None):
        super().__init__(self, name, 'boolean', False, default)


"""
# -*-ModelMetaclass的工作主要是为一个数据库表映射成一个封装的类做准备：
# ***读取具体子类 的映射信息
# 创造类的时候，排除对Model类的修改
# 在当前类中查找所有的类属性(attrs)，如果找到Field属性，就将其保存到__mappings__的dict中，
# 同时从类属性中删除Field(防止实例属性遮住类的同名属性)
# 将数据库表名保存到__table__中
"""


class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        # 排序Model类本身
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        # 若没有设定表名则使用类名
        tableName = attrs.get('__table__', None) or name
        logging('found model:%s (table:%s)' % (name, tableName))
        # 获取所有的Field 和主键名
        mappings = dict()
        fileds = list()
        primaryKey = None
        for k, v in attrs.items():
            if isinstance(v, Filed):
                logging.info('found mapping:%s===>%s' % (k, v))
                mappings[k] = v
                # 找到了主键
                if v.primary_key:
                    if primaryKey:
                        raise RuntimeError('duplicate primary key for field:%s' % k)
                    primaryKey = k
                else:
                    fileds.append(k)
        if not primaryKey:
            raise RuntimeError('primary key not found...')

        # 从类属性中删除Field属性
        for k in mappings:
            attrs.pop(k)
        # 给字段加上 ``
        escaped_fileds = list(map(lambda f: '`%s`' % f, fileds))

        # 保存属性和列的映射关系
        attrs['__mappings__'] = mappings
        # 保存表名
        attrs['__table__'] = tableName
        # 保存主键
        attrs['__primary_key__'] = primaryKey
        # 除主键之外的属性名
        attrs['__fields__'] = fileds
        # 构造默认的select insert update delete 语句
        attrs['__select__'] = 'select `%s`,%s from `%`' % (primaryKey, ','.join(escaped_fileds), tableName)
        attrs['__insert__'] = 'insert into %s (`%s`,%s) VALUES (%s)' % (
            tableName, ','.join(escaped_fileds), primaryKey, ','.join('?' * len(mappings)))

        attrs['__delete__'] = 'delete from `%s` where %s=?' % (tableName, primaryKey)

        attrs['__update__'] = 'update %s set %s where %s=?' % (
            tableName, ','.join(map(lambda z: '`%s`=?' % (mappings.get(z).name or z), fileds)), primaryKey)
        return type.__new__(cls, name, bases, attrs)


"""
# 定义ORM所有映射的基类：Model
# Model类的任意子类可以映射一个数据库表
# Model类可以看作是对所有数据库表操作的基本定义的映射
# 基于字典查询形式
# Model从dict继承，拥有字典的所有功能，同时实现特殊方法__getattr__和__setattr__，能够实现属性操作
# 实现数据库操作的所有方法，定义为class方法，所有继承自Model都具有数据库操作方法
"""


class Model(dict, metaclass=ModelMetaclass):
    def __init__(self, **kwargs):
        super(Model, self).__init__(**kwargs)

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError('has no attribute :%s' % item)

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key)

    def getDefaultValue(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                # callable 检查对象是否可以调用
                value = field.default() if callable(field.default) else field.default
                logging.debug('useing default vale for %s:%s' % (key, value))
                setattr(self, key, value)
        return value

    @asyncio.coroutine
    def save(self):
        args = list(map(self.getDefaultValue, self.__fields__))
        args.append(self.getValue(self, self.__primary_key__))
        rows = yield from execute(self.__insert__, args)
        if rows != 1:
            logging.error('failed to insert record:affected rows:%s' % rows)

    @asyncio.coroutine
    def update(self):
        args = list(map(self.getValue, self.__fields))
        args.append(self.getValue(self, self.__primary_key__))
        rows = yield from execute(self.__update__, args)
        if rows != 1:
            logging.error('failed to update record:affected rows:%s' % rows)

    @asyncio.coroutine
    def delete(self):
        args = list()
        args.append(self.getValue(self, self.__primary_key__))
        rows = yield from execute(self.__delete__, args)
        if rows != 1:
            logging.error('failed to delete record:affected rows:%s' % rows)

    """
     where ：查询条件
     args：查询参数 list 类型
     **kwargs：排序，limit 等
    """

    @classmethod
    @asyncio.coroutine
    def findAll(self, where=None, args=None, **kwargs):
        sql = [self.__select__]
        if where and args:
            sql.append('where')
            sql.append(where)

        orderBy = kwargs.get('orderBy', None)
        if orderBy:
            sql.append("order by")
            sql.append(orderBy)

        limit = kwargs.get('limit', None)
        if limit:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?', '?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value:%s' % str(limit))
        rs = yield from select(' '.join(sql), args)
        return [self(**r) for r in rs]
