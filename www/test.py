# coding=utf-8

l = ','.join(map(lambda z: '`%s`=?' % z, ('a', 'b', 'c')))
print(l)


class Person(object):
    def sayHello(self):
        print("hello ....")


p = Person()

print(callable(p.sayHello))
