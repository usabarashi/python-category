def test_either():
    from typing import Any

    from category import Left, Right

    assert 0 == Left[int, Any](0).value
    assert 0 == Right[Any, int](0).value
    assert False is bool(Left[int, Any](0))
    assert True is bool(Right[Any, int](0))
    assert True is Left[int, Any](0).is_left()
    assert False is Left[int, Any](0).is_right()
    assert False is Right[Any, int](0).is_left()
    assert True is Right[Any, int](0).is_right()


def test_either_do():
    from typing import Any, Generator

    from category import Either, Left, Right

    @Either.do
    def left_context() -> Generator[Either[None, int], Any, int]:
        one = yield from Right[None, int](1)()
        two = 2
        three = yield from Left[None, int](None)()
        return one + two + three

    assert None is left_context().value
    assert False is bool(left_context())
    assert True is left_context().is_left()
    assert False is left_context().is_right()
    assert Left[None, int](None).value == left_context().value
    assert (
        Left[int, int](0).value
        == left_context()
        .fold(left=lambda value: 0, right=lambda value: value * 2)
        .value
    )

    @Either.do
    def right_context() -> Generator[Either[None, int], Any, int]:
        one = yield from Right[None, int](1)()
        two = 2
        three = yield from Right[None, int](3)()
        return one + two + three

    assert 6 == right_context().value
    assert True is bool(right_context())
    assert False is right_context().is_left()
    assert True is right_context().is_right()
    assert Right[None, int](6) == right_context()
    assert Right[None, int](12) == right_context().fold(
        left=lambda value: 0, right=lambda value: value * 2
    )


def test_try():
    from category import Failure, Success

    assert Failure is type(Failure(Exception()))
    assert ValueError is type(Failure(ValueError()).value)
    assert 0 == Success(0).value
    assert True is bool(Success(0))
    assert False is bool(Failure(Exception()))
    assert True is Success(0).is_success()
    assert False is Success(0).is_failure()
    assert False is Failure(Exception()).is_success()
    assert True is Failure(Exception()).is_failure()


def test_try_hold():
    from category import Failure, Success, Try

    @Try.hold
    def multi_context(value: int) -> int:
        if not value:
            raise Exception("error")
        return value

    assert Failure is type(multi_context(0))
    assert Exception is type(multi_context(0).value)
    assert Success is type(multi_context(1))
    assert 1 == multi_context(1).value
    assert False is bool(multi_context(0))
    assert True is bool(multi_context(1))
    assert True is multi_context(0).is_failure()
    assert False is multi_context(0).is_success()
    assert False is multi_context(1).is_failure()
    assert True is multi_context(1).is_success()


def test_try_do():
    from typing import Any, Generator

    from category import Failure, Success, Try

    @Try.do
    def failure_context() -> Generator[Any, Any, int]:
        one = yield from Success(1)()
        two = 2
        three = yield from Failure(ValueError())()
        return one + two + three

    assert Failure is type(failure_context())
    assert ValueError is type(failure_context().value)
    assert False is bool(failure_context())
    assert False is failure_context().is_success()
    assert True is failure_context().is_failure()
    assert Failure is type(
        failure_context().fold(
            failure=lambda value: EOFError(), success=lambda value: value * 2
        )
    )

    @Try.do
    def success_context() -> Generator[Any, Any, int]:
        one = yield from Success(1)()
        two = 2
        three = yield from Success(3)()
        return one + two + three

    assert Success(6) == success_context()
    assert 6 == success_context().value
    assert True is bool(success_context())
    assert True is success_context().is_success()
    assert False is success_context().is_failure()
    assert Success[int](12) == success_context().fold(
        failure=lambda value: ValueError(), success=lambda value: value * 2
    )

    @Try.hold
    def multi_context(value: int) -> int:
        if not value:
            raise Exception("error")
        return value

    @Try.do
    def mix_failure_context() -> Generator[Any, Any, int]:
        success = yield from multi_context(1)()
        _ = yield from multi_context(0)()
        return success

    assert Failure is type(mix_failure_context())
    assert Exception is type(mix_failure_context().value)

    @Try.do
    def mix_success_context() -> Generator[Any, Any, int]:
        one = yield from multi_context(1)()
        two = 2
        three = yield from multi_context(3)()
        return one + two + three

    assert Success(6) == mix_success_context()
    assert 6 == mix_success_context().value


def test_future():
    import asyncio
    import concurrent.futures
    from typing import Optional

    from category import Future

    loop = asyncio.get_event_loop()

    @Future.hold
    def context(
        value: int = 0,
        /,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        executor: Optional[concurrent.futures.ThreadPoolExecutor] = None,
    ) -> int:
        return value

    with concurrent.futures.ThreadPoolExecutor() as executor:
        assert False is bool(context(1)(loop=loop, executor=executor))


def test_future_hold():
    import asyncio
    import concurrent.futures
    from typing import Optional

    from category import Failure, Future, Success

    loop = asyncio.get_event_loop()

    @Future.hold
    def context(
        value: int = 0,
        /,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        executor: Optional[concurrent.futures.ThreadPoolExecutor] = None,
    ) -> int:
        if not value:
            raise Exception("Future Failure")
        return value

    with concurrent.futures.ThreadPoolExecutor() as executor:
        assert Future is type(context(0)(loop=loop, executor=executor))
        assert Failure is type(context(0)(loop=loop, executor=executor).on_complete())
        assert Exception is type(
            context(0)(loop=loop, executor=executor).on_complete().value
        )

    with concurrent.futures.ThreadPoolExecutor() as executor:
        assert Future is type(context(1)(loop=loop, executor=executor))
        assert Success is type(context(1)(loop=loop, executor=executor).on_complete())
        assert 1 == context(1)(loop=loop, executor=executor).on_complete().value


def test_future_do():
    import asyncio
    import concurrent.futures
    from typing import Any, Generator, Optional

    from category import Failure, Future, Success

    loop = asyncio.get_event_loop()

    @Future.hold
    def context(
        value: int = 0,
        /,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        executor: Optional[concurrent.futures.ThreadPoolExecutor] = None,
    ) -> int:
        if not value:
            raise Exception("Future Failure")
        return value

    with concurrent.futures.ThreadPoolExecutor() as executor:

        @Future.do
        def mix_failure_context(
            *,
            loop: asyncio.AbstractEventLoop,
            executor: concurrent.futures.ThreadPoolExecutor,
        ) -> Generator[Any, Any, int]:
            one = yield from context(1)(loop=loop, executor=executor)()
            two = 2
            three = yield from context(0)(loop=loop, executor=executor)()
            return one + two + three

        assert Future is type(mix_failure_context()(loop=loop, executor=executor))
        assert Failure is type(
            mix_failure_context()(loop=loop, executor=executor).on_complete()
        )
        assert Exception is type(
            mix_failure_context()(loop=loop, executor=executor).on_complete().value
        )

        @Future.do
        def mix_success_context(
            *,
            loop: asyncio.AbstractEventLoop,
            executor: concurrent.futures.ThreadPoolExecutor,
        ) -> Generator[Any, Any, int]:
            one = yield from context(1)(loop=loop, executor=executor)()
            two = 2
            three = yield from context(3)(loop=loop, executor=executor)()
            return one + two + three

        assert Future is type(mix_success_context()(loop=loop, executor=executor))
        assert Success is type(
            mix_success_context()(loop=loop, executor=executor).on_complete()
        )
        assert (
            6 == mix_success_context()(loop=loop, executor=executor).on_complete().value
        )
