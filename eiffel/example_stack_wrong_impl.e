note
	description: "A stack example wrong implementation."
	author: "J. Férard"
	copyright: "Python Toy Contract (C) J. Férard 2020"

class
	EXAMPLE_STACK_WRONG_IMPL

inherit

	EXAMPLE_STACK

create
	make

feature {NONE}

	arr: LINKED_LIST [INTEGER]

feature {NONE} -- Initialization

	make
			-- Initialization for `Current'.
		do
			size := 0
			create arr.make
		end

feature

	push (e: INTEGER)
		do
			arr.extend (e)
			arr.forth
			size := size + 1
		end

feature -- Pop an element from the stack

	pop: INTEGER
		do
			Result := arr.item
			arr.remove
				-- size := size - 1
		end

feature -- Top element

	top: INTEGER
		do
			Result := arr.item
		end

feature -- Size of the stack

	size: INTEGER

end
