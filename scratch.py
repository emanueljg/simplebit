from functools import wraps



# dirty metaclass hack that injects decorator in a 
class Meta(type):
	STUFF = {}
	@classmethod
	def __prepare__(metacls, name, bases):
		#print(name)
		def deco(arg):
			def inner_deco(f):
				Meta.STUFF[arg] = f
				def wrapped(*args, **kwargs):
					return f(*args, **kwargs)
				return wrapped
			return inner_deco
			#Meta.STUFF.append(inner_deco)
			#Meta.STUFF.append((inner_deco, wrapped, f))

		
		return {'deco': deco, 'STUFF': Meta.STUFF}


class A(metaclass=Meta):

	@deco('x')
	def foo(self):
		print('foo')

	@deco('y')
	@deco('z')
	def bar(self):
		print('bar')

	def do(self, key):
		return self.STUFF[key](self)

a = A()
#a.foo()
#a.foo()
print(Meta.STUFF)
A.STUFF['y'](a)
#Meta.STUFF['x'](a)
#Meta.STUFF[0]()
#print(Meta.STUFF())
#a.foo()
#a.foo()
#a.foo()
#a.foo()
#a.do('y')

#print(Deco.STUFF)
#Deco.STUFF['y']()
