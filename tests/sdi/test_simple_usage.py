import pytest

from sdi import Injector


@pytest.fixture
def inject() -> Injector:
    return Injector()


def test_injector_fresh_instance(inject: Injector):
    assert len(inject._callables) == 0
    assert len(inject._singletons) == 0


def test_injector_no_return_type(inject: Injector):
    with pytest.raises(ValueError) as excinfo:

        @inject.transient
        def get_str():
            return ""

    assert "requires a return type annotation" in str(excinfo.value)


def test_inject_transient(inject: Injector):
    class Cat:
        def __init__(self, age: int):
            self.age = age

    @inject.transient
    def get_cat() -> Cat:
        return Cat(9)

    @inject.resolve
    def meow(cat=inject(Cat)) -> Cat:
        assert isinstance(cat, Cat)
        assert cat.age == 9

        return cat

    assert meow() is not meow()


def test_inject_singleton(inject: Injector):
    class Cat:
        def __init__(self, age: int):
            self.age = age

    @inject.singleton
    def get_cat() -> Cat:
        return Cat(9)

    @inject.resolve
    def meow(cat=inject(Cat)) -> Cat:
        assert isinstance(cat, Cat)
        assert cat.age == 9

        return cat

    assert meow() is meow()


def test_inject_unknown(inject: Injector):
    class Cat:
        def __init__(self, age: int):
            self.age = age

    def get_cat() -> Cat:
        return Cat(9)

    @inject.resolve
    def meow(cat=inject(Cat)) -> Cat:
        assert isinstance(cat, Cat)
        assert cat.age == 9

        return cat

    with pytest.raises(ValueError) as excinfo:
        meow()

    assert "No callables registered for type" in str(excinfo.value)


def test_inject_various_injections(inject: Injector):
    class User: ...

    class Database:
        @inject.resolve
        def __init__(self, url: str, user=inject(User)):
            self.url = url
            self.users = [user]

    @inject.transient
    def get_user() -> User:
        return User()

    @inject.singleton
    def get_database() -> Database:
        return Database("localhost:6379")

    @inject.resolve
    def retrieve_first_user(database=inject(Database)) -> User:
        assert isinstance(database, Database)
        assert database.url == "localhost:6379"
        assert len(database.users) == 1

        return database.users[0]

    assert isinstance(retrieve_first_user(), User)
