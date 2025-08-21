from multipledispatch import dispatch


@dispatch(int, int)
def fun(arg, arg2):
    print("This is a number", arg)


@dispatch(str, str)
def fun(arg, arg2):
    print("This is a str", arg)


@dispatch(float)
def fun(arg):
    print("This is a float", arg)


fun(3, 4)


fun(3.1)
fun("three point one", "yam an")
