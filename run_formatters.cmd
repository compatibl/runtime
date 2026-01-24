@echo off

call activate

echo.
echo Remove unused imports using autoflake
autoflake cl --check --quiet
autoflake cl --in-place
autoflake stubs --check --quiet
autoflake stubs --in-place
autoflake tests --check --quiet
autoflake tests --in-place

echo.
echo Format using isort
isort cl
isort stubs
isort tests

echo.
echo Format using black
black -q cl --config=pyproject.toml
black -q stubs --config=pyproject.toml
black -q tests --config=pyproject.toml

