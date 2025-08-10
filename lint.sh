echo "linting:"
ruff check --fix

echo "\nsorting imports:"
ruff check --select I --fix

echo "\nformating:"
ruff format

echo "\ntype-checking:"
pyright
