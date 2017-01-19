#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2017/1/15 下午11:25
# @Author  : lost
# @Site    : 
# @File    : Models.py
# @Software: PyCharm

import time, uuid

from www.orm import StringFiled, IntegerFiled, BooleanFiled, TextFiled, FloatFiled, Model


def next_id():
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)


class User(Model):
    __table__ = 'user'
    id = StringFiled(primary_key=True, default=next_id, column_type='varchar(50)')
    email = StringFiled(column_type='varchar(50)')
    password = StringFiled(column_type='varchar(50)')
    admin = BooleanFiled()
    name = StringFiled(column_type='varchar(50)')
    image = StringFiled(column_type='varchar(500)')
    create_at = FloatFiled(default=time.time)


class Blog(Model):
    __table__ = 'blog'
    id = StringFiled(primary_key=True, default=next_id, column_type='varchar(50)')
    user_id = StringFiled(column_type='varchar(50)')
    user_name = StringFiled(column_type='varchar(50)')
    user_image = StringFiled(column_type='varchar(500)')
    name = StringFiled(column_type='varchar(50)')
    # 摘要
    summary = StringFiled(column_type='varchar(200)')
    create_at = FloatFiled(default=time.time)


class Comment(Model):
    __table__ = 'comment'
    id = StringFiled(primary_key=True, default=next_id, column_type='varchar(50)')
    blog_id = StringFiled(column_type='varchar(50)')
    user_id = StringFiled(column_type='varchar(50)')
    user_name = StringFiled(column_type='varchar(50)')
    user_image = StringFiled(column_type='varchar(500)')
    content = TextFiled()
    created_at = FloatFiled(default=time.time)


