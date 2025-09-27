import pytest

from gladi import Injector


@pytest.fixture
def inject() -> Injector:
    return Injector()


def test_injector_fresh_instance(inject: Injector):
    assert len(inject._registry) == 0
    assert len(inject._callables) == 0
    assert len(inject._instances) == 0


def test_injector_no_return_type(inject: Injector):
    with pytest.raises(ValueError) as excinfo:

        @inject.transient
        def get_str():
            return ""

    assert "requires a return type annotation" in str(excinfo.value)


def test_injector_no_registration(inject: Injector):
    class Cat:
        def __init__(self):
            pass

    with pytest.raises(ValueError) as excinfo:

        @inject.resolve
        def meow(cat=inject(Cat)):
            return cat

        meow()

    assert "is not registered as an injectable" in str(excinfo.value)


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


def test_inject_scoped(inject: Injector):
    class Cat:
        def __init__(self, age: int):
            self.age = age

    class Dog:
        _cat: Cat

        def __init__(self, age: int):
            self.age = age

    @inject.scoped
    def get_cat() -> Cat:
        return Cat(9)

    @inject.scoped
    def get_dog(cat=inject(Cat)) -> Dog:
        dog = Dog(3)
        dog._cat = cat

        return dog

    @inject.resolve
    def play(cat=inject(Cat), dog=inject(Dog)) -> None:
        assert cat is dog._cat

    play()


def test_inject_scoped_again(inject: Injector):
    class Person:
        def __init__(self, age: int):
            self.age = age

    class Cat:
        _person: Person

        def __init__(self, age: int):
            self.age = age

    class Dog:
        _person: Person

        def __init__(self, age: int):
            self.age = age

    @inject.scoped
    def get_person() -> Person:
        return Person(30)

    @inject.scoped
    def get_cat(person=inject(Person)) -> Cat:
        cat = Cat(9)
        cat._person = person

        return cat

    @inject.scoped
    def get_dog(person=inject(Person)) -> Dog:
        dog = Dog(3)
        dog._person = person

        return dog

    @inject.resolve
    def play(cat=inject(Cat), dog=inject(Dog)) -> None:
        assert cat._person is dog._person

    play()


def test_inject_transient(inject: Injector):
    class Cat:
        def __init__(self, age: int):
            self.age = age

    class Dog:
        _cat: Cat

        def __init__(self, age: int):
            self.age = age

    @inject.transient
    def get_cat() -> Cat:
        return Cat(9)

    @inject.transient
    def get_dog(cat=inject(Cat)) -> Dog:
        dog = Dog(3)
        dog._cat = cat

        return dog

    @inject.resolve
    def play(cat=inject(Cat), dog=inject(Dog)) -> None:
        assert isinstance(cat, Cat) and isinstance(dog._cat, Cat)
        assert cat is not dog._cat

    play()


def test_inject_mixed(inject: Injector):
    class Cat:
        def __init__(self, age: int):
            self.age = age

    class Dog:
        _cat: Cat

        def __init__(self, age: int):
            self.age = age

    class Person:
        _cat: Cat
        _dog: Dog

        def __init__(self, age: int):
            self.age = age

    @inject.singleton
    def get_cat() -> Cat:
        return Cat(9)

    @inject.scoped
    def get_dog(cat=inject(Cat)) -> Dog:
        dog = Dog(3)
        dog._cat = cat

        return dog

    @inject.transient
    def get_person(cat=inject(Cat), dog=inject(Dog)) -> Person:
        person = Person(30)
        person._cat = cat
        person._dog = dog

        return person

    @inject.resolve
    def cat_and_dog(cat=inject(Cat), dog=inject(Dog)) -> tuple[Cat, Dog]:
        return (cat, dog)

    (cat1, dog1) = cat_and_dog()
    (cat2, dog2) = cat_and_dog()

    assert cat1 is dog1._cat
    assert cat1 is cat2
    assert cat1 is dog2._cat
    assert dog1 is not dog2

    @inject.resolve
    def everything(
        cat=inject(Cat), dog=inject(Dog), person=inject(Person)
    ) -> tuple[Cat, Dog, Person]:
        return (cat, dog, person)

    (cat1, dog1, person1) = everything()
    (cat2, dog2, person2) = everything()

    assert cat1 is dog1._cat
    assert cat1 is person1._cat
    assert dog1 is person1._dog
    assert cat2 is dog2._cat
    assert cat2 is person2._cat
    assert dog2 is person2._dog
    assert person1 is not person2


def test_inject_various_injections(inject: Injector):
    class User: ...

    class Database:
        @inject.resolve
        def __init__(self, url: str, user=inject(User)):
            self.url = url
            self.users = [user]

    @inject.scoped
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
