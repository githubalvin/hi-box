
def check_respond(data):
    """返回数据检查"""
    if "msg" in data:
        raise RuntimeError(data["msg"])
    return data["data"]


if "_SINGLE_OBJ" not in globals():
    _SINGLE_OBJ = {}


class SingletonMeta(type):

    def __new__(cls, name ,bases, attrs):
        init_func = attrs.get("__init__", None)
        if init_func is None and bases:
            init_func = getattr(bases[0], "__init__", None)

        if init_func is not None:
            def __myinit__(obj, *args, **kwargs):
                if obj.__class__.single_inited:
                    return
                _SINGLE_OBJ[obj.__class__.__name__] = obj
                init_func(obj, *args, **kwargs)
                obj.__class__.single_inited = True
            attrs["__init__"] = __myinit__
        return super(SingletonMeta, cls).__new__(cls, name ,bases, attrs)


class Singleton(metaclass=SingletonMeta):
    """单例类"""

    def __new__(cls, *args, **kwargs):
        if cls.__name__ not in _SINGLE_OBJ:
            obj = super(Singleton, cls).__new__(cls, *args, **kwargs)
            obj.__class__.single_inited = False
            _SINGLE_OBJ[cls.__name__] = obj
        return _SINGLE_OBJ[cls.__name__]

