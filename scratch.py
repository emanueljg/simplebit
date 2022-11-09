from functools import wraps



# dirty metaclass hack that injects fundamental decorator functionality
class ActionRegistrar(type):
	actions = defaultdict(defaultdict(list))

	@classmethod
	def __prepare__(metacls, name, bases):
		def action(arg):
			def inner_action(f):
				Meta.STUFF[arg] = f
				def wrapped(*args, **kwargs):
					return f(*args, **kwargs)
				return wrapped
			return inner_deco
		
		return {'action': action, 'actions': ActionRegistrar.actions}


class A(metaclass=ActionRegistrar):

	@action('x')
	def foo(self):
		print('foo')

	@action('y')
	@action('z')
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
