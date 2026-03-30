# settings (/docs/python-reference/packages/phlo-traefik/phlo_traefik/settings)



Traefik service configuration constants.

This module defines default configuration values for the Traefik reverse
proxy service integration with the Phlo platform.

All values defined here can be overridden through environment variables
or configuration files in the Phlo settings system.

Example:

> > > from phlo\_traefik.settings import TRAEFIK\_HTTP\_PORT\_DEFAULT
> > > print(TRAEFIK\_HTTP\_PORT\_DEFAULT)
> > > 80

<PyAttribute name="&#x22;TRAEFIK_HTTP_PORT_DEFAULT&#x22;" type="&#x22;int&#x22;" value="&#x22;80&#x22;" />

<PyAttribute name="&#x22;TRAEFIK_DOMAIN_DEFAULT&#x22;" type="&#x22;str&#x22;" value="&#x22;'phlo.localhost'&#x22;" />
