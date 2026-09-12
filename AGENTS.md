# Agents

This repository is the **graphify-postpass** product
(`https://github.com/pleware/graphify-postpass`).

Public and company-agnostic. A consumer or host name inside this kit is
contamination, not configuration. Project-specific bridges (host-language
function names) belong in the consuming repository.

Drafts and backlog do not live here.

Ignite plants this package into the `graphifyy` tool env. Do not vendor
Graphify. Do not patch Graphify's `site-packages`.

After a behaviour change:

```sh
uv run pytest
```
