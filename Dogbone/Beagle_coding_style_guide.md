Beagle coding style-guide
=====================

Python style rules
-------------------------

1. **Do not terminate your lines with semi-colons** and do not use semi-colons to put two commands on the same line.

2. Maximum line length should be **80 characters**.

3. Indent your code blocks with **4 spaces**.

4. If a class inherits from no other base classes, **explicitly inherit from object**. This also applies to nested classes.

5. Use **TODO comments** for code that is temporary, a short-term solution, or good-enough but not perfect

6. Imports should be on separate lines.

		Yes: import os
		     import sys

		No:  import sys, os

		Yes: from subprocess import Popen, PIPE

7. Organising imports: Imports are always put at the top of the file, just after any module comments and docstrings, and before module globals and constants.

	Imports should be grouped in the following order:

	    standard library imports
	    related third party imports
	    local application/library specific imports

	You should put a blank line between each group of imports.

8. Generally use only **one statement per line.**
9. **Naming conventions**

		module_name
		package_name
		ClassName
		ExceptionName
		function_name
		GLOBAL_CONSTANT_NAME
		global_var_name
		instance_var_name
		function_parameter_name
		local_var_name


10. Even a file meant to be used as a script should be importable and a mere import should not have the side effect of executing the script's main functionality. The main functionality should be in a main() function.

11. Blank lines:
	+ Separate top-level function and class definitions with two blank lines.
	+ Method definitions inside a class are separated by a single blank line.

	+ Use blank lines in functions, sparingly, to indicate logical sections.

12. Whitespace:

    Immediately inside parentheses, brackets or braces.

	    Yes: spam(ham[1], {eggs: 2})
	    No:  spam( ham[ 1 ], { eggs: 2 } )

    Immediately before a comma, semicolon, or colon:

	    Yes: if x == 4: print x, y; x, y = y, x
	    No:  if x == 4 : print x , y ; x , y = y , x

    However, in a slice the colon acts like a binary operator, and should have equal amounts on either side (treating it as the operator with the lowest priority). In an extended slice, both colons must have the same amount of spacing applied. Exception: when a slice parameter is omitted, the space is omitted.

    Yes:

	    ham[1:9], ham[1:9:3], ham[:9:3], ham[1::3], ham[1:9:]
	    ham[lower:upper], ham[lower:upper:], ham[lower::step]
	    ham[lower+offset : upper+offset]
	    ham[: upper_fn(x) : step_fn(x)], ham[:: step_fn(x)]
	    ham[lower + offset : upper + offset]

    No:

	    ham[lower + offset:upper + offset]
	    ham[1: 9], ham[1 :9], ham[1:9 :3]
	    ham[lower : : upper]
	    ham[ : upper]

    Immediately before the open parenthesis that starts the argument list of a function call:

	    Yes: spam(1)
	    No:  spam (1)

    Immediately before the open parenthesis that starts an indexing or slicing:

	    Yes: dct['key'] = lst[index]
	    No:  dct ['key'] = lst [index]

    More than one space around an assignment (or other) operator to align it with another.

    Yes:

	    x = 1
	    y = 2
	    long_variable = 3

    No:

	    x             = 1
	    y             = 2
	    long_variable = 3


	Don't use spaces around the = sign when used to indicate a keyword argument or a default parameter value.

	Yes:

		def complex(real, imag=0.0):
		    return magic(r=real, i=imag)

	No:

		def complex(real, imag = 0.0):
		    return magic(r = real, i = imag)

13. Long strings

	If a string is too long and has to expand on multiple lines, use the more conveninet method of the following two:

	Yes:

		'''here
		comes the long string'''

	Note that here the line break and the indentation of the second line are included in the string

	Yes:

		('first line'
		 'second line')

	No:

		'first line \
		 second line'

14. Other Recommendations

	+ Use is not operator rather than not ... is. While both expressions are functionally identical, the former is more readable and preferred.

	Yes:

		if foo is not None:

	No:

		if not foo is None:

	+ When implementing ordering operations with rich comparisons, it is best to implement all six operations
        (`__eq__`, `__ne__`, `__lt__`, `__le__`, `__gt__`, `__ge__`) rather than relying on other code to only
        exercise a particular comparison.

		To minimize the effort involved, the ``functools.total_ordering()`` decorator provides a tool to generate missing comparison methods.

	+ Always use a def statement instead of an assignment statement that binds a lambda expression directly to an identifier.

	Yes:

		def f(x): return 2*x

	No:

		f = lambda x: 2*x

	+ When catching exceptions, mention specific exceptions whenever possible instead of using a bare except: clause.

	For example, use:

		try:
		    import platform_specific_module
		except ImportError:
		    platform_specific_module = None





Testing
----------

1. Use ``unittests`` for testing separate modules/functions/classes (Sentence Annotation, Party Extraction, etc ...)
2. Create functional tests for full product features (User Registration, Contract Upload, etc ...)
3. For testing the UI, Selenium tests or if appropriate other Javascript test framework

Code commit Policy
---------------------------

1. Don't work on ``master`` branch
2. ``master`` branch should be clean
3. Create branches for features/fixes. Before merging to ``master``, ask a peer for a code review and manual testing. Be sure the tests pass.
4. ``release`` branch is used for publishing code to the production environment
