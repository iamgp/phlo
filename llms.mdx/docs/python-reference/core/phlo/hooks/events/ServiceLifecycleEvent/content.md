# ServiceLifecycleEvent (/docs/python-reference/core/phlo/hooks/events/ServiceLifecycleEvent)



Lifecycle event emitted around service start/stop phases.

These events track the lifecycle of Phlo-managed services (PostgreSQL,
MinIO, Trino, etc.) as they are started, stopped, or undergo configuration
changes.

Attributes [#attributes]

<PyAttribute name="&#x22;service_name&#x22;" type="&#x22;str&#x22;" value="null">
  Name of the service being managed.
</PyAttribute>

<PyAttribute name="&#x22;project_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Name of the project context.
</PyAttribute>

<PyAttribute name="&#x22;project_root&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Root directory of the project.
</PyAttribute>

<PyAttribute name="&#x22;container_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Docker container name if applicable.
</PyAttribute>

<PyAttribute name="&#x22;phase&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Lifecycle phase ("start", "stop", "configure", etc.).
</PyAttribute>

<PyAttribute name="&#x22;status&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Current status of the phase ("started", "completed", "failed").
</PyAttribute>

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;field(default_factory=dict)&#x22;">
  Additional service-specific information.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, *, event_type, version=EVENT_VERSION, timestamp=_utc_now(), tags=dict(), correlation=HookCorrelation(), service_name, project_name=None, project_root=None, container_name=None, phase=None, status=None, metadata=dict()) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event_type&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;version&#x22;" type="&#x22;str&#x22;" value="&#x22;EVENT_VERSION&#x22;" />

    <PyParameter name="&#x22;timestamp&#x22;" type="&#x22;datetime&#x22;" value="&#x22;_utc_now()&#x22;" />

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;correlation&#x22;" type="&#x22;HookCorrelation&#x22;" value="&#x22;HookCorrelation()&#x22;" />

    <PyParameter name="&#x22;service_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;project_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;project_root&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;container_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;phase&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;status&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;dict()&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
