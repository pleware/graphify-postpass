# graphify-postpass

House extractors that run **after** [Graphify](https://github.com/Graphify-Labs/graphify)
rebuilds `graphify-out/graph.json`.

Graphify has no plugin API for extra languages. A patch inside its
`site-packages` dies on `uv tool upgrade`. This package writes a second
pass onto the graph instead: nodes carry `_origin` other than `"ast"`, so
Graphify's AST rebuild keeps them.

Ignite plants this into the same `graphifyy` environment that owns
`graphify-out/.graphify_python`. Run it with that interpreter.

```sh
graphify-postpass --root .
# or
python -m graphify_postpass --root .
```

## What it extracts

| Extractor | Files | Edges |
| --- | --- | --- |
| Twig | `*.twig` | `extends`, `includes`, `imports`, `defines` (blocks) |

Composition only. Project-specific function bridges (a host language calling
into PHP, Python, …) stay in the consuming repository as data, not here.

Regex extraction, same shape as Graphify's own Blade and Razor extractors.
No tree-sitter dependency.

## Install

Ignite (`pins/tools.sh`) installs it next to `graphifyy`:

```sh
uv tool install --with git+https://github.com/pleware/graphify-postpass.git@v0.1.0 \
  "graphifyy[ollama,sql]"
```

Or, in an environment that already has Graphify:

```sh
uv pip install --python "$(cat graphify-out/.graphify_python)" \
  git+https://github.com/pleware/graphify-postpass.git@v0.1.0
```

`graphify.ids.make_id` must come from that same interpreter. Do not invent
node ids.

## After a Graphify rebuild

`graphify update` can drop edges whose endpoints moved. Re-run the post-pass
so composition edges come back. The merge is idempotent: it deletes the
previous `_origin` contribution first.

## License

Apache License 2.0. Graphify itself is Apache-2.0; this companion matches it.
