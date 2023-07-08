A toy project. Attempt to use dynamic nature of Python to implement 
programming by contract.

Despite being a toy project, the goal is to have a working implementation. But
performance is less important than documentation.

# References
A wonderful book by B. Meyer: [Object-Oriented Software Construction, 2nd 
Edition](https://www.eiffel.org/doc/eiffel/Object-Oriented_Software_Construction%2C_2nd_Edition).

The reference implementation of Eiffel at https://www.eiffel.org/.

The [PEP 316 -- Programming by Contract for Python](
https://www.python.org/dev/peps/pep-0316/)

Some (serious) contract libraries in Python:
* https://github.com/Parquery/icontract: uses decorators + lambdas;
* https://github.com/AndreaCensi/contracts: uses decorator + custom syntax; 

# Python Toy Contract goal
I was wondering whether it was easy to implement a toy "programming by 
contract" feature in Python.

Function contracts can easily be achieved with the `assert` statement:

    def f(x, y, z):
        assert <precondition>, "Precondition violation"
        <code>
        assert <postcondition>, "Postcondition violation"

Hence I focused on class contracts, since they are the most interesting: 
invariants, precondtions and postconditions should be inherited from a parent
class if they exist.

## An Eiffel version of the example
Bonus: I wrote an Eiffel version of the example. I'm far from being an Eiffel 
expert, hence the code is probably clumsy. Please fill an issue if you know 
how to improve the code.

# Usage
Assertions are defined at class level:

    class X(Contract):
        def __invariant__(self):
            assert <my test>, <msg>

        def func(self, x, y, z):
            def __require__(self, x, y, z):
                assert <my test>, <msg>
                
            def __ensure__(self, ret, old, x, y, z):
                assert <my test>, <msg>

            <body of the function>

When deriving the class, invariants and postconditions may be strenghtened, 
but preconditions may only be weakened:

    class Y(X):
        def __invariant__(self):
            assert <my test>, <msg>

        def func(self, x, y, z):
            def __require_else__(self, x, y, z):
                assert <my test>, <msg>
                
            def __ensure_then__(self, ret, old, x, y, z):
                assert <my test>, <msg>

            <body of the function, don't forget too call the super class>

# Running the tests
To run the tests of the Python version, you have to type:

    python-toy-contract$ python3 -m pytest
    
To run the test of the Eiffel version:

    python-toy-contract$ pushd eiffel/
    python-toy-contract/eiffel$ ec -config eiffel/python-toy-contract.ecf -tests
    python-toy-contract$ popd
    
the Python tests pass, because of `assertRaises` tests. The Eiffel tests fail.

# Design
## Assertions using `assert` statement 
Unlike other libraries:

* assertions are not coded as lambdas or strings, but using plain old 
`assert` statements.
* I did not use decorators but a method (for invariants) and nested 
functions (for pre and post conditions). 

These functions are executed before and after the body of the function. If an
assertions fails, you have the whole stacktrace.

## When assertions are disabled
Contracts are enabled only if assertions are enabled. This is true by design,
but there is a shortcut with virtually no performance penaly: 
`ContractMeta.__new__` simply does not create a version of the class with 
contracts. 

---

Unlike many other languages, but like Eiffel assertions, Python assertions are
enabled by default. They are disabled [when the command line option `-O` is set
](https://docs.python.org/3/reference/simple_stmts.html#the-assert-statement).
This can be checked with the `__debug__` constant:

    python/python-toy-contract$ python3.7
    >>> __debug__
    True
    >>> assert False
    Traceback (most recent call last):
    ...
    AssertionError

But:

    jferard@jferard-Z170XP-SLI:~/prog/python/python-toy-contract$ python3.7 -O
    Python 3.7.5 (default, Nov  7 2019, 10:50:52) 
    [GCC 8.3.0] on linux
    Type "help", "copyright", "credits" or "license" for more information.
    >>> __debug__
    False
    >>> assert False
    >>> # nothing

## Non paranoid mode
The default mode is the "paranoid mode": invariants are checked after 
`__init__` (is the initial state ok) and then *before* and *after* each 
function call (along with pre or post conditions). You could imagine that 
checking the invariant *after* a function call is sufficient, but it's very
easy to alter manually the state of an object:

> We don't use the term "private" here, since no attribute is really 
> private in Python -- [*PEP 8 - Designing for Inheritance*](https://www.python.org/dev/peps/pep-0008/#designing-for-inheritance)  

Though, there is a "non paranoid mode". Invariants are checked only after 
method calls:

    class X(Contract):
        __paranoid__ = False


# Implementation
There are some challenges:
* explore the class hierarchy to find the `__invariant__` methods in parent
classes, using the [MRO](https://www.python.org/download/releases/2.3/mro/);
* explore the class hierarchy to find, for each public method, the 
`__require__` and `__ensure__` nested functions, following the MRO;
* be able to turn off assertions inside assertions.
* check all the invariants and postconditions, but allow a weakening of 
preconditions. 

## Find the `__invariant__` method in parent classes
We just follow the class `__mro__` attribute.

## Find for each public method, the `__require__` and `__ensure__` nested functions
This is less easy. First, we need a list of public method, whether they are in 
a class or its parents. This is what `dir()` was made for.

Now, we have the names of the public methods, we follow the MRO until we
find a method in a class `C`. Then, we switch to `C`s MRO to go up until
we meet the `object` class. Obviously, the list of methods (and classes)
is different for each function.

Then, we take this list and look for nested `__require__` and `__ensure__`
functions. We can build a list of those nested functions, for each name of 
a public function.

## Turn off assertions
If you use a method inside an assertion (pre/postcondition or invariant), then
you are in great risk to trigger an endless loop. Example: the invariant is 
checked after each method, but it calls a method `m`. Then, inside the 
invariant, you'll call the invariant and you are stuck.

Usually, we use a trigger: turn off the assertions, check the assertions, turn
on the assertions. But Python is dynamic, hence I choose to have 
two classes: `contracted_C`, with assertions, `relaxed_C` with no assertions. 

When we check the assertions, we change the class of the object to relaxed,
when we execute the method, we change the class of the object to contracted. 
This is achieved using a [metaclass](
https://docs.python.org/3/reference/datamodel.html#metaclasses): for each 
declared class, two classes are create and linked: 

* `contracted_C.__relaxed__ = relaxed_C`
* `relaxed_C.__contracted__ = contracted_C`

The class `contracted_C` is returned.

## Check assertions - weakening of preconditions
Invariants and postcondtions are all checked in reverse order (from parents to 
children). This allows to raise the first infraction from the most generic 
class. 

Preconditions are checked in reverse order, until we find a precondition that is
met. If none of the preconditions is met, then the precondition fails. Python 
Toy Contract returns the violation of the precondition in the most generic
class.

# Some thoughts on programming by contract
## What went wrong?
The first version of Eiffel was released in 1986, more than 30 years ago. 
Design by contract is, in my mind, a genius idea. Most 
languages have only a poor, defaced version of contracts, that is the `assert` 
keyword. So what went wrong?

Frankly, I don't know, but the "Do you eat your own dog food" is enlightening:
I read carefully the code, thinking of invariants, pre or post conditions, and
the conclusion is unequivocal: the only place where I need a state is, when
looking for assertions, I have to ensure that one and only `__require__`
preceeds one or many `__require_else__` (same for `__require__` and 
`__ensure_then__`). And three `assert` statements seemed enough, because
the real question here is: do I have all the assertions? and not: are these 
assertions in the right order?

If I can draw a conclusion from such a small example, it would be the 
following.

B. Meyer insists on correctness of programs. But that's not always 
the primary concern of program makers. It may be performance (some games), 
cost, ease of development, ... But even if correctness is the primary goal, 
correctness cannot always be expressed using contracts:

* some classes are only disguised structures (you know, those 
classes that have only getters and setters), helper classes like factories or 
builders (no real state).
* some classes are too dependent of a global state (they need 
tests, not invariants). Think of the classes that process an input.
* some classes do not belong to a hierarchy, and you don't need to inherit
pre/post conditions and invariants: `assert` is enough.

Don't get me wrong, I would like to have real contracts in Python, Kotlin, 
Java, Rust, ..., but they didn't seem a panacea to languages designers.

## Liskov substitution principle
Remember the LSP?

> Subtype Requirement: Let *ϕ(x)* be a property provable about objects *x* 
of type *T*. Then *ϕ(y)* should be true for objects *y* of type *S* where *S* is a subtype of *T*. 

Basically, in a given program, I should be able to replace a instance of a 
class by an instance of any subclass of this class. If it doesn't work the 
subclass is *not* a subtype, because it doesn't follow the semantic of the
parent type, just it's syntax. In other word, subclassing is about method 
signatures, while subtyping is about method behavior.

With design by contract, assertions are part of the signature that should 
carry at least a part of the semantic. Thus, subtyping should be closer 
to subclassing.
