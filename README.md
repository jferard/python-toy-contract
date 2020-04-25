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

# Running the tests
## An Eiffel version of the example
Bonus: I wrote an Eiffel version of the example. I'm far from being an Eiffel 
expert, hence the code is probably clumsy. Please fill an issue if you know 
how to improve the code.

## Let's go
To run the tests of the Python version, you have to type:

    python-toy-contract$ python3.7 -m pytest
    
To run the test of the Eiffel version:

    python-toy-contract$ pushd eiffel/
    python-toy-contract/eiffel$ ec -config eiffel/python-toy-contract.ecf -tests
    python-toy-contract$ popd
    
the Python tests pass, because of `assertRaises` tests. The Eiffel tests fail.

# Design
Unlike other libraries:
 
* assertions are not coded as lambdas or strings, but using plain old 
`assert` statements.
* I did not use decorators but a method (for invariants) and nested 
functions (for pre and post conditions). 

These functions are executed before and after the body of the function:

    class X(metaclass=Contract):
        def __invariant__(self):
            assert <my test>, <msg>

        def func(self, x, y, z):
            def __require__(self, x, y, z):
                assert <my test>, <msg>
                
            def __ensure__(self, ret, old, x, y, z):
                assert <my test>, <msg>

            <body of the function>

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
TODO.