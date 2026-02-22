# Punq is Archived

When I originally wrote this library, I was in the middle of writing Cosmic
Python. I wanted to show how a dependency container could simplify wiring up a
complex application, but I was disappointed by the available options which
tended to adopt a config-heavy style a la PHP rather than a simpler,
type-oriented style. 

I went through the code of Funq, fired up pytest, and set about TDDing myself a
DI library.

I have never used this library in production. Mostly, that's because when I left
MADE.com, I began using serverless architectures, where a Lambda handler is a
natural composition root, that only needs to build a small number of
dependencies. The itch I had when I started this library has been well and truly
scratched: I have shown an example of how to build a simple DI container, using
type hints for registration; the code is relatively straightforward; there is
100% code coverage. Another engineer, better motivated, can take this code -
which is free of license encumberance - and build whatever complex thing they
need. I wish them all the best.

I would have liked to implement full type-safety, but Python as of 3.11 makes
that a little difficult. Perhaps, when the type checking tools catch up, I'll
have a go for fun.
I do not want to make this library more fully-featured, because then it loses
its value as a learning tool. I am gratified that people have used and found
benefit from my small experiment, and will bless whatever forks might take over.

I have completely failed to maintain this code, because it is not useful to me,
and because I want it to be a simple example for others who might build more
useful tools in future. I am relucantly archiving it. So long, and thanks for
all the stars.

# Punq

[![Release](https://img.shields.io/github/v/release/bobthemighty/punq)](https://img.shields.io/github/v/release/bobthemighty/punq)
[![Build status](https://img.shields.io/github/actions/workflow/status/bobthemighty/punq/main.yml?branch=main)](https://github.com/bobthemighty/punq/actions/workflows/main.yml?query=branch%3Amain)
[![Tests](https://codecov.io/github/bobthemighty/punq/graph/badge.svg?token=52hQhaggnk)](https://codecov.io/github/bobthemighty/punq)
[![Commit activity](https://img.shields.io/github/commit-activity/m/bobthemighty/punq)](https://img.shields.io/github/commit-activity/m/bobthemighty/punq)
[![License](https://img.shields.io/github/license/bobthemighty/punq)](https://img.shields.io/github/license/bobthemighty/punq)

<!-- quick_start -->

An unintrusive library for dependency injection in modern Python.
Inspired by [Funq][1], Punq is a dependency injection library you can understand.

- No global state
- No decorators
- No weird syntax applied to arguments
- Small and simple code base with 100% test coverage and developer-friendly comments.

## Installation

Punq is available on the [cheese shop][2]

```shell
pip install punq
```

Documentation is available on [Github pages][3].

## Quick Start

Punq avoids global state, so you must explicitly create a container in the entrypoint of your application:

```python
import punq

container = punq.Container()
```

Once you have a container, you can register your application's dependencies. In the simplest case, we can register any arbitrary object with some key:

```python
container.register("connection_string", instance="postgresql://...")
```

We can then request that object back from the container:

```python
conn_str = container.resolve("connection_string")
```

Usually, though, we want to register some object that implements a useful service.:

```python
class ConfigReader:
    def get_config(self):
        pass

class EnvironmentConfigReader(ConfigReader):
    def get_config(self):
        return {
        "logging": {
            "level": os.env.get("LOGGING_LEVEL", "debug")
        },
        "greeting": os.env.get("GREETING", "Hello world")
        }

container.register(ConfigReader, EnvironmentConfigReader)
```

Now we can `resolve` the `ConfigReader` service, and receive a concrete implementation:

```python
config = container.resolve(ConfigReader).get_config()
```

If our application's dependencies have their _own_ dependencies, Punq will inject those, too:

```python
class Greeter:
    def greet(self):
        pass


class ConsoleGreeter(Greeter):
    def __init__(self, config_reader: ConfigReader):
        self.config = config_reader.get_config()

    def greet(self):
        print(self.config['greeting'])


container.register(Greeter, ConsoleGreeter)
container.resolve(Greeter).greet()

```

If you just want to resolve an object without having any base class, that's okay:

```python
class Greeter:
    def __init__(self, config_reader: ConfigReader):
        self.config = config_reader.get_config()

    def greet(self):
        print(self.config['greeting'])

container.register(Greeter)
container.resolve(Greeter).greet()
```

And if you need to have a singleton object for some reason, we can tell punq to register a specific instance of an object:

```python
class FileWritingGreeter:
    def __init__(self, path, greeting):
        self.path = path
        self.message = greeting
        self.file = open(self.path, 'w')

    def greet(self):
        self.file.write(self.message)


one_true_greeter = FileWritingGreeter("/tmp/greetings", "Hello world")
container.register(Greeter, instance=one_true_greeter)
```

You might not know all of your arguments at registration time, but you can provide them later:

```python
container.register(Greeter, FileWritingGreeter)
greeter = container.resolve(Greeter, path="/tmp/foo", greeting="Hello world")

```

Conversely, you might want to provide arguments at registration time, without adding them to the container:

```python
container.register(Greeter, FileWritingGreeter, path="/tmp/foo", greeting="Hello world")
```

[1]: https://github.com/jlyonsmith/Funq
[2]: https://pypi.org/project/punq/
[3]: https://bobthemighty.github.io/punq/
[4]: https://github.com/fpgmaas/cookiecutter-uv

<!-- end_quick_start -->

Fuller documentation is available on [Github pages][3]

Github workflows, nox configuration, and linting gratefully stolen from [CookieCutter UV][4]
