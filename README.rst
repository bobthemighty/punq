Punq
====

An unintrusive library for dependency injection in modern Python.

.. image:: https://travis-ci.org/bobthemighty/punq.svg?branch=master
    :target: https://travis-ci.org/bobthemighty/punq
.. image:: https://img.shields.io/codecov/c/github/bobthemighty/punq.svg?style=flat
    :target https://codecov.io/gh/bobthemighty/punq
.. image:: https://readthedocs.org/projects/punq/badge/?version=latest
    :target: https://punq.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

Inspired by `Funq`_, Punq is a dependency injection library you can understand.

- No global state
- No decorators
- No weird syntax applied to arguments
- Small and simple code base with 100% test coverage and developer-friendly comments.

Installation
------------

Punq is available on the `cheese shop`_. ::

   pip install punq

Documentation is available on `Read the docs`_.

Quick Start
-----------

Punq avoids global state, so you must explicitly create a container in the entrypoint of your application::

   import punq
    
   container = punq.Container()

Once you have a container, you can register your application's dependencies. In the simplest case, we can register any arbitrary object with some key::

   container.register("connection_string", "postgresql://...")

We can then request that object back from the container::

   conn_str = container.resolve("connection_string")

Usually, though, we want to register some object that implements a useful service.::

   class ConfigReader:

      def get_config(self):
         pass
 
   class EnvironmentConfigReader(ConfigReader):

      def get_config(self):
         return {
            "logging": {
               "level": os.env.get("LOGGING_LEVEL", "debug")
            }
            "greeting": os.env.get("GREETING", "Hello world")
         }

   container.register(ConfigReader, EnvironmentConfigReader)

Now we can `resolve` the `ConfigReader` service, and receive a concrete implementation::

   config = container.resolve(ConfigReader).get_config()

If our application's dependencies have their _own_ dependencies, Punq will inject those, too::

   class Greeter:

      def greet(self):
         pass


   class ConsoleGreeter:

      def __init__(self, config_reader: ConfigReader):
         self.config = config_reader.get_config()

      def greet(self):
         print(self.config['greeting'])


   container.register(Greeter)
   container.resolve(Greeter).greet()
         
If you just want to resolve an object without having any base class, that's okay::

   class Greeter:

      def __init__(self, config_reader: ConfigReader):
         self.config = config_reader.get_config()

      def greet(self):
         print(self.config['greeting'])

   container.register(Greeter)
   container.resolve(Greeter).greet()
         
And if you need to have a singleton object for some reason, we can tell punq to register a specific instance of an object.::

   class FileWritingGreeter:

      def __init__(self, path, greeting):
         self.path = path
         self.message = greeting

         self.file = open(self.path, 'w')

      def greet(self):
         self.file.write(self.message)


   one_true_greeter = FileWritingGreeter("/tmp/greetings", "Hello world")
   container.register(Greeter, instance=one_true_greeter)


You might not know all of your arguments at registration time, but you can provide them later.::

   container.register(Greeter, FileWritingGreeter)
   greeter = container.resolve(Greeter, path="/tmp/foo", greeting="Hello world")

Conversely, you might want to provide arguments at registration time, without adding them to the container::

   container.register(Greeter, FileWritingGreeter, path="/tmp/foo", greeting="Hello world")
   
Fuller documentation is available on `Read the docs`_.

.. _cheese shop: https://pypi.org/project/punq/
.. _Read the docs: http://punq.readthedocs.io/en/latest/ 
.. _Funq: https://github.com/jlyonsmith/Funq
