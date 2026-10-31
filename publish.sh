#!/bin/bash
# Publie les deux SDK depuis le serveur (Termius, en root) :
#   bash /root/easyad-sdk/publish.sh npm      → @easyyad/bot-sdk sur npm
#   bash /root/easyad-sdk/publish.sh pypi     → easyyad sur PyPI
# Les identifiants ne sont jamais écrits dans ce dossier : ils sont demandés, puis oubliés.
set -e
trap 'echo "❌ Échec à la ligne $LINENO : $BASH_COMMAND"' ERR
DIR=$(cd "$(dirname "$0")" && pwd)

case "${1:-}" in
  npm)
    cd "$DIR/javascript"
    npm test
    read -s -p "Jeton npm (Granular Access Token, droit « Read and write ») : " NPM_TOKEN; echo
    printf '//registry.npmjs.org/:_authToken=%s\n' "$NPM_TOKEN" > "$DIR/.npmrc-tmp"
    npm publish --access public --userconfig "$DIR/.npmrc-tmp"
    rm -f "$DIR/.npmrc-tmp"; unset NPM_TOKEN
    echo "✅ Publié : https://www.npmjs.com/package/@easyyad/bot-sdk"
    ;;
  pypi)
    cd "$DIR/python"
    python3 -m unittest discover -s tests
    python3 -m venv /tmp/easyad-pub && /tmp/easyad-pub/bin/pip install -q --upgrade build twine
    rm -rf dist && /tmp/easyad-pub/bin/python -m build
    /tmp/easyad-pub/bin/twine check dist/*
    read -s -p "Jeton PyPI (commence par pypi-) : " PYPI_TOKEN; echo
    TWINE_USERNAME=__token__ TWINE_PASSWORD="$PYPI_TOKEN" /tmp/easyad-pub/bin/twine upload dist/*
    unset PYPI_TOKEN; rm -rf /tmp/easyad-pub build ./*.egg-info
    echo "✅ Publié : https://pypi.org/project/easyyad/"
    ;;
  *)
    echo "Usage : bash publish.sh npm | pypi"; exit 1 ;;
esac
