note
	description: "Eiffel tests for Python Toy Contract"
	author: "J. Férard"
	copyright: "Python Toy Contract (C) J. Férard 2020"

class
	EXAMPLE_TEST_SET

inherit

	EQA_TEST_SET

feature -- New test routine

	test_empty_stack
		local
			l_stack: EXAMPLE_STACK_IMPL
			i: INTEGER
		do
			create l_stack.make
			i := l_stack.pop
		end

feature -- New test routine

	test_wrong_implementation
		local
			l_stack: EXAMPLE_STACK_WRONG_IMPL
			i: INTEGER
		do
			create l_stack.make
			l_stack.push (1)
			i := l_stack.pop
		end

feature -- New test routine

	test_even_stack_0
		local
			l_stack: EXAMPLE_EVEN_STACK_IMPL
		do
			create l_stack.make
			l_stack.push (0)
		end

feature -- New test routine

	test_even_stack_1
		local
			l_stack: EXAMPLE_EVEN_STACK_IMPL
		do
			create l_stack.make
			l_stack.push (1)
		end

end
