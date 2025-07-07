def precheck(func):
    def wrapper():
        func()
    return wrapper