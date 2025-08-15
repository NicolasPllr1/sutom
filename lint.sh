echo "linting:"
ruff check --fix

echo "\nsorting imports:"
ruff check --select I --fix

echo "\nformating:"
ruff format

# https://github.com/hukkin/mdformat?tab=readme-ov-file#command-line-usage
echo "\nFormating markdown"
uvx mdformat --wrap 80 .

echo "\ntype-checking:"
pyright
