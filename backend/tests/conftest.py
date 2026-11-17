"""项目测试公共配置。"""
import asyncio
import inspect

import pytest


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem):
    """在不依赖 pytest-asyncio 的前提下执行异步测试函数。"""
    test_function = pyfuncitem.obj
    if not inspect.iscoroutinefunction(test_function):
        return None

    fixture_names = pyfuncitem._fixtureinfo.argnames
    kwargs = {name: pyfuncitem.funcargs[name] for name in fixture_names}
    asyncio.run(test_function(**kwargs))
    return True


def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: 标记异步测试函数")
