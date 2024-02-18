# -*- coding: utf8 -*-

# Allows delegates to subscribe for the event and to be called when event is triggered.
#--------------------------------------------------------------------------------------------------
class Event(object):
	__slots__ = ('__delegates', )
	# manager - event manager that is used to clear all events thereby break all references.
	# Clearing events without event manager:
	#	onEvent1 = Event()
	#	onEvent2 = Event()
	#	...
	#	onEvent1.clear()
	#	onEvent2.clear()
	#
	# Clearing events with event manager:
	#	em = EventManager()
	#	onEvent1 = Event(em)
	#	onEvent2 = Event(em)
	#	...
	#	em.clear()
	#----------------------------------------------------------------------------------------------
	def __init__(self, manager = None):
		self.__delegates = list()
		if manager is not None:
			manager.register(self)

	# operator (). Calls delegates.
	#----------------------------------------------------------------------------------------------
	def __call__(self, *args):
		for delegate in self.__delegates[:]:
			delegate( *args )

	# operator +=. Adds delegate.
	#----------------------------------------------------------------------------------------------
	def __iadd__(self, delegate):
		if delegate not in self.__delegates:
			self.__delegates.append(delegate)
		return self

	# operator -=. Removes delegate.
	#----------------------------------------------------------------------------------------------
	def __isub__(self, delegate):
		if delegate in self.__delegates:
			self.__delegates.remove(delegate)
		return self

	def __contains__(self, item):
		return item in self.__delegates

	def __iter__(self):
		for delegate in self.__delegates:
			yield delegate
		
	#----------------------------------------------------------------------------------------------
	def add(self, delegate):
		if delegate not in self.__delegates:
			self.__delegates.append(delegate)

	# operator -=. Removes delegate.
	#----------------------------------------------------------------------------------------------
	def remove(self, delegate):
		if delegate in self.__delegates:
			self.__delegates.remove(delegate)

	# operator len. Get number of subscribed delegate
	#----------------------------------------------------------------------------------------------
	def __len__(self):
		return len( self.__delegates )

	# Removes all delegates.
	#----------------------------------------------------------------------------------------------
	def clear(self):
		del self.__delegates[:]

	def __repr__(self):
		return "Event(%s):%s" % (len(self.__delegates), repr(self.__delegates))

# Similar to Event. Difference is Handler allows only one delegate to be subscribed.
# One event manager could be used both for handlers and events.
#--------------------------------------------------------------------------------------------------
class Handler:

	# manager - event manager that is used to clear all handlers thereby break all references.
	#----------------------------------------------------------------------------------------------
	def __init__(self, manager = None):
		self.__delegate = None
		if manager is not None:
			manager.register(self)

	# operator (). Calls delegates.
	#----------------------------------------------------------------------------------------------
	def __call__(self, *args):
		if self.__delegate is not None:
			return self.__delegate(*args)
		return None

	# Sets the delegate to call on the event.
	#----------------------------------------------------------------------------------------------
	def set(self, delegate):
		self.__delegate = delegate

	# Same as set(None).
	#----------------------------------------------------------------------------------------------
	def clear(self):
		self.__delegate = None

# Event manager that is used to clear all events thereby break all references.
#--------------------------------------------------------------------------------------------------
class EventManager:

	#----------------------------------------------------------------------------------------------
	def __init__(self):
		# List of registered events
		self.__events = []

	#----------------------------------------------------------------------------------------------
	def register(self, event):
		self.__events.append(event)

	#----------------------------------------------------------------------------------------------
	def clear(self):
		for event in self.__events:
			event.clear()
