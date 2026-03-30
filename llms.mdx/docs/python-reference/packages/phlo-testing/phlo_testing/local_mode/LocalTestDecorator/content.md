# LocalTestDecorator (/docs/python-reference/packages/phlo-testing/phlo_testing/local_mode/LocalTestDecorator)



Decorator to mark tests that should use local mode.

Example:

> > > @local\_test
> > > ... def test\_my\_asset():
> > > ...     # Runs with mocked resources
> > > ...     pass

Functions [#functions]

<PyFunction name="&#x22;__call__&#x22;" type="&#x22;(self, func) -> Any&#x22;">
  Apply decorator.

  <PySourceCode>
    ```python
    def __call__(self, func: Any) -> Any:
        """Apply decorator.

        Args:
            func: Function to wrap.

        Returns:
            Wrapped function that runs inside local test mode.

        """

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Run the wrapped callable inside local test mode.

            Args:
                *args: Positional arguments passed to the wrapped callable.
                **kwargs: Keyword arguments passed to the wrapped callable.

            Returns:
                The wrapped callable result.

            """
            with local_test_mode():
                return func(*args, **kwargs)

        return wrapper
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;func&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Function to wrap.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Wrapped function that runs inside local test mode.
  </PyFunctionReturn>
</PyFunction>
