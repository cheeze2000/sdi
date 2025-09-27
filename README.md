# gladi

## Overview

Import the injector. This is the only import needed.

```py
from gladi import inject
```

The library provides 4 decorators:

- `@inject.singleton`: creates a singleton from a callable that instantiates the class in its return type
- `@inject.scoped`: same as singleton, but the callable gets called once per request
- `@inject.transient`: same as singleton, but it gets called on every request
- `@inject.resolve`: signals to the library that dependencies in parameters need to be resolved
	- using `@inject.singleton`, `@inject.scoped` or `@inject.transient` implies this

## Simple Usage

Assuming we have a class to inject,

```py
class Database: ...
```

create a function (or callable) with no user-provided arguments that returns a `Database` instance.

```py
def get_database() -> Database:
	return Database(
		host=...,
		port=...,
	)
```

Mark the callable with a decorator. In this case, a singleton would be appropriate.

```py
@inject.singleton
def get_database() -> Database: ...
```

`Database` class is now an injectable (as a singleton).

```py
async retrieve_user(
	user_id: int,
	database = inject(Database),
): ...
```

Lastly, signal that the `retrieve_user` function needs its dependencies to be resolved with the `@inject.resolve` decorator.

```py
@inject.resolve
async retrieve_user(
	user_id: int,
	database = inject(Database),
): ...

await retrieve_user(33)
```
