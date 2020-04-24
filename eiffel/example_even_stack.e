note
	description: "An even stack example. All elements should be even."
	author: "J. F�rard"
	copyright: "Python Toy Contract (C) J. F�rard 2020"

deferred class
	EXAMPLE_EVEN_STACK

inherit

	EXAMPLE_STACK

invariant
	top_is_even: size = 0 or top \\ 2 = 0

end
