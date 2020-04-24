note
	description: "A stack example."
	author: "J. Férard"
	copyright: "Python Toy Contract (C) J. Férard 2020"

deferred class
	EXAMPLE_STACK

feature -- Push an element on the stack

	push (e: INTEGER)
		deferred
		ensure
			one_more: size = old size + 1
			element_on_top: e = top
		end

feature -- Pop an element from the stack

	pop: INTEGER
		require
			not_empty: size >= 1
		deferred
		ensure
			one_less: size = old size - 1
			ret_top: Result = old top
		end

feature -- Top element

	top: INTEGER
		require
			not_empty: size >= 1
		deferred
		end

feature -- Size of the stack

	size: INTEGER
		deferred
		end

invariant
	positive_size: size >= 0

end
