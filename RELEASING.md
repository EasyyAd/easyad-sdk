# Publier une version (mainteneurs)

La publication est automatique : poussez une étiquette de version et GitHub Actions teste puis
publie les deux paquets sur npm et PyPI (une version déjà en ligne est sautée, donc rejouer un
tag ne casse rien).

```bash
# 1. Montez la version aux trois endroits :
#    javascript/package.json, python/pyproject.toml, python/easyyad/__init__.py
# 2. Commitez, puis :
git tag v1.0.1
git push --tags
```

Suivez l'exécution dans l'onglet **Actions** du dépôt.

## Configuration (une seule fois, sur le dépôt GitHub)

1. **npm** — créez l'organisation `easyyad` sur npmjs.com (le paquet est `@easyyad/bot-sdk`),
   générez un jeton « Granular Access Token » limité à ce paquet avec le droit *Read and write*,
   et mettez-le dans *Settings → Secrets and variables → Actions* sous le nom `NPM_TOKEN`.
2. **PyPI** — aucun jeton : sur pypi.org → *Your account → Publishing → Add a pending publisher*,
   déclarez le projet `easyyad`, ce dépôt, le fichier `publish.yml` et l'environnement `pypi`.

Les jetons vivent dans les secrets GitHub, jamais dans le code. `publish.sh` reste une solution
de repli manuelle depuis un serveur.
