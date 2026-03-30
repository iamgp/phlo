# FAQ (/docs/reference/faq)



Because those parts of the stack usually need environment-specific configuration after install. Most other packages are infrastructure or runtime components, and their main behavior is covered in [Packages](../packages/index.md).

Why are there multiple API surfaces? [#why-are-there-multiple-api-surfaces]

Because they solve different problems:

* `phlo-api`: Phlo-native control-plane and product-specific behavior
* `PostgREST`: relational REST exposure
* `Hasura`: GraphQL exposure
* `OpenMetadata`: metadata and discovery surface

Why is Python Reference separate from Reference? [#why-is-python-reference-separate-from-reference]

Because generated symbol docs and hand-written reference serve different purposes. `Reference` explains stable platform behavior. `Python Reference` exposes docstrings, signatures, and module-level detail.

Why is Observatory not the center of the docs? [#why-is-observatory-not-the-center-of-the-docs]

Because Observatory is one UI surface within the platform, not the platform itself.

Why so many packages? [#why-so-many-packages]

Because Phlo is intentionally modular. Packages let teams install only the runtime pieces they need while keeping extension points explicit.
