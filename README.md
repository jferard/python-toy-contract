A toy project. Endeavour to use dynamic nature of Python to implement 
programming by contract.

# References
A wonderful book by B. Meyer: [Object-Oriented Software Construction, 2nd Edition](https://www.eiffel.org/doc/eiffel/Object-Oriented_Software_Construction%2C_2nd_Edition).

The reference implementation of Eiffel at https://www.eiffel.org/.

The [PEP 316 -- Programming by Contract for Python](https://www.python.org/dev/peps/pep-0316/)

Some (serious) contract libraries in Python:
* https://github.com/Parquery/icontract: uses decorators + lambdas;
* https://github.com/AndreaCensi/contracts: uses decorator + custom syntax; 

# Python Toy Contract
I was wondering whether it was easy to implement a toy 
"programming by contract" feature in Python.

I focused on class contracts, since they are the most interesting: 
invariants, precondtions and postconditions should be inherited. 

These assertions are coded as plain old `assert` directives, not as
functions as in other libraries. These functions are executed before
and after the body of the function. 

Usage:

    class X(metaclass=Contract):
        def __invariant__(self):
            assert <my test>, <msg>

        def func(self, x, y, z):
            def __require__(self, x, y, z):
                assert <my test>, <msg>
                
            def __ensure__(self, ret, old, x, y, z):
                assert <my test>, <msg>

            <body of the function>
    

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
    python-toy-contract$ popd eiffel/
    
the Python tests pass, because of `assertRaises` tests. The Eiffel tests fail.

# TODO
Explain the code.    
