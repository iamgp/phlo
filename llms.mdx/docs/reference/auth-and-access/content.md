# Auth And Access Model (/docs/reference/auth-and-access)



Model [#model]

<Mermaid
  chart="flowchart TD
    principal[&#x22;User or service principal&#x22;] --> authn[&#x22;Authentication provider&#x22;]
    authn --> session[&#x22;Authenticated session&#x22;]
    session --> authz[&#x22;Authorization policy backend&#x22;]
    authz --> surfaces[&#x22;API and UI surfaces&#x22;]
    authz --> data[&#x22;Data and governance backends&#x22;]"
/>

Responsibilities [#responsibilities]

* authentication decides who the caller is
* authorization decides what that caller may do
* serving layers like `phlo-api`, `Hasura`, and `PostgREST` enforce those decisions in different ways
* governance and backend systems may apply their own secondary controls

Where To Look [#where-to-look]

* [Security](../setup/security.md) for operator setup and posture
* [Python Reference](../python-reference/index.mdx) for capability-level auth interfaces
* [API Surfaces](api-surfaces.md) for how access shows up across external entry points
