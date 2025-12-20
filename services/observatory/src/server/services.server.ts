/**
 * Services Server Functions
 *
 * Server-side functions for service discovery and Docker management.
 * Reads service.yaml files and interacts with Docker Compose.
 */

import { exec } from 'node:child_process'
import { existsSync } from 'node:fs'
import { readFile, readdir } from 'node:fs/promises'
import { join } from 'node:path'
import { promisify } from 'node:util'
import { createServerFn } from '@tanstack/react-start'

import { parse as parseYaml } from 'yaml'
import { authMiddleware } from '@/server/auth.server'

const execAsync = promisify(exec)

// Types for service definitions
export interface EnvVar {
  name: string
  value: string
  description?: string
  secret: boolean
}

export interface ServiceDefinition {
  name: string
  description: string
  category: string
  default: boolean
  image?: string
  dependsOn: Array<string>
  ports: Array<{ host: number; container: number; description?: string }>
  envVars: Array<EnvVar>
  url?: string
}

export interface DockerContainerStatus {
  name: string
  service: string
  status: 'running' | 'stopped' | 'unhealthy' | 'starting' | 'unknown'
  health?: string
  ports?: string
}

export interface ServiceWithStatus extends ServiceDefinition {
  containerStatus: DockerContainerStatus | null
}

// Get the services directory path
// In Docker: /app/services
// Locally: process.cwd() is services/observatory/, parent is services/
const getServicesPath = (): string => {
  if (process.env.SERVICES_PATH) {
    return process.env.SERVICES_PATH
  }
  // Check if running in Docker
  const dockerPath = '/app/services'
  if (existsSync(dockerPath)) {
    return dockerPath
  }
  // Local development: cwd is services/observatory/, go up one level to services/
  const localPath = join(process.cwd(), '..')
  if (existsSync(join(localPath, 'core'))) {
    return localPath
  }
  // Fallback: maybe cwd is project root
  const projectServicesPath = join(process.cwd(), 'services')
  if (existsSync(projectServicesPath)) {
    return projectServicesPath
  }
  return localPath
}

// Path to .env file
const getEnvPath = (): string => {
  if (process.env.ENV_FILE_PATH) {
    return process.env.ENV_FILE_PATH
  }
  const dockerPath = '/app/.env'
  if (existsSync(dockerPath)) {
    return dockerPath
  }
  // Local: .env is at project root (parent of services/)
  const localPath = join(process.cwd(), '..', '..', '.env')
  if (existsSync(localPath)) {
    return localPath
  }
  // Fallback: maybe cwd is project root
  const projectEnvPath = join(process.cwd(), '.env')
  if (existsSync(projectEnvPath)) {
    return projectEnvPath
  }
  return localPath
}

/**
 * Parse a service.yaml file
 */
async function parseServiceYaml(
  filePath: string,
): Promise<ServiceDefinition | null> {
  try {
    const content = await readFile(filePath, 'utf-8')
    const data = parseYaml(content)

    if (!data || !data.name) {
      return null
    }

    // Extract ports from compose.ports
    const ports: Array<{
      host: number
      container: number
      description?: string
    }> = []
    if (data.compose?.ports) {
      for (const portMapping of data.compose.ports) {
        // Format: "${HOST_PORT:-default}:container" or "host:container"
        const match = portMapping.match(
          /\$\{([^:}]+):-?(\d+)\}:(\d+)|(\d+):(\d+)/,
        )
        if (match) {
          if (match[1]) {
            // Variable format: ${VAR:-default}:container
            ports.push({
              host: parseInt(match[2], 10),
              container: parseInt(match[3], 10),
              description: match[1],
            })
          } else {
            // Direct format: host:container
            ports.push({
              host: parseInt(match[4], 10),
              container: parseInt(match[5], 10),
            })
          }
        }
      }
    }

    // Extract env vars from env_vars section
    const envVars: Array<EnvVar> = []
    if (data.env_vars) {
      for (const [varName, config] of Object.entries(data.env_vars)) {
        const cfg = config as {
          default?: string | number
          description?: string
          secret?: boolean
        }
        envVars.push({
          name: varName,
          value: String(cfg.default ?? ''),
          description: cfg.description,
          secret: cfg.secret ?? false,
        })
      }
    }

    // Determine URL from first port
    const firstPort = ports[0]
    const url = firstPort ? `http://localhost:${firstPort.host}` : undefined

    return {
      name: data.name,
      description: data.description || '',
      category: data.category || 'core',
      default: data.default ?? false,
      image: data.image,
      dependsOn: data.depends_on || [],
      ports,
      envVars,
      url,
    }
  } catch {
    return null
  }
}

/**
 * Discover all services from service.yaml files
 */
async function discoverServices(): Promise<Array<ServiceDefinition>> {
  const servicesPath = getServicesPath()
  const services: Array<ServiceDefinition> = []

  // Known category directories that contain service subdirectories
  const categoryDirs = ['admin', 'api', 'bi', 'core', 'observability']

  try {
    const entries = await readdir(servicesPath)

    for (const entry of entries) {
      // Skip hidden entries and non-relevant directories
      if (entry.startsWith('.') || entry === 'node_modules') {
        continue
      }

      const entryPath = join(servicesPath, entry)

      // Check if this is a category directory (contains service subdirs)
      if (categoryDirs.includes(entry)) {
        try {
          const serviceNames = await readdir(entryPath)
          for (const serviceName of serviceNames) {
            if (serviceName.startsWith('.')) continue
            const yamlPath = join(entryPath, serviceName, 'service.yaml')
            const service = await parseServiceYaml(yamlPath)
            if (service) {
              services.push(service)
            }
          }
        } catch {
          // Directory read failed, skip it
        }
      } else {
        // Check if this directory has a direct service.yaml (like observatory)
        const directYaml = join(entryPath, 'service.yaml')
        const service = await parseServiceYaml(directYaml)
        if (service) {
          services.push(service)
        }
      }
    }
  } catch (error) {
    console.error('Error discovering services:', error)
  }

  return services.sort((a, b) => {
    // Sort by category, then by name
    if (a.category !== b.category) {
      return a.category.localeCompare(b.category)
    }
    return a.name.localeCompare(b.name)
  })
}

/**
 * Parse .env file and merge with service defaults
 */
async function loadEnvValues(): Promise<Record<string, string>> {
  const envPath = getEnvPath()
  const values: Record<string, string> = {}

  try {
    const content = await readFile(envPath, 'utf-8')

    for (const line of content.split('\n')) {
      const trimmed = line.trim()
      if (trimmed && !trimmed.startsWith('#')) {
        const eqIndex = trimmed.indexOf('=')
        if (eqIndex > 0) {
          const key = trimmed.slice(0, eqIndex)
          const value = trimmed.slice(eqIndex + 1)
          values[key] = value
        }
      }
    }
  } catch {
    // .env file may not exist
  }

  return values
}

/**
 * Get Docker container status for all services
 */
export const getDockerStatus = createServerFn().handler(
  async (): Promise<Array<DockerContainerStatus>> => {
    try {
      // Use docker ps to get ALL running containers (not compose-specific)
      const { stdout } = await execAsync('docker ps -a --format json')

      const containers: Array<DockerContainerStatus> = []

      // Docker outputs one JSON object per line
      for (const line of stdout.trim().split('\n')) {
        if (!line) continue

        try {
          const container = JSON.parse(line)

          // Parse status - Docker returns "running", "exited", "created", etc.
          let status: DockerContainerStatus['status'] = 'unknown'
          const rawState = (
            container.State ||
            container.Status ||
            ''
          ).toLowerCase()

          if (rawState.includes('running')) {
            status = container.Health === 'unhealthy' ? 'unhealthy' : 'running'
          } else if (
            rawState.includes('starting') ||
            rawState.includes('created')
          ) {
            status = 'starting'
          } else {
            status = 'stopped'
          }

          // Get service name from docker compose label
          const labels = container.Labels || ''
          const serviceMatch = labels.match(
            /com\.docker\.compose\.service=([^,]+)/,
          )
          const serviceName = serviceMatch ? serviceMatch[1] : ''

          if (serviceName) {
            containers.push({
              name: container.Names || container.Name || '',
              service: serviceName,
              status,
              health: container.Health,
              ports: container.Ports,
            })
          }
        } catch {
          // Skip invalid JSON lines
        }
      }

      return containers
    } catch (error) {
      console.error('Error getting Docker status:', error)
      return []
    }
  },
)

/**
 * Get all services with their definitions and Docker status
 */
export const getServices = createServerFn().handler(
  async (): Promise<Array<ServiceWithStatus>> => {
    // Load data in parallel
    const [services, containers, envValues] = await Promise.all([
      discoverServices(),
      getDockerStatus(),
      loadEnvValues(),
    ])

    // Create a map of service name to container status
    const containerMap = new Map<string, DockerContainerStatus>()
    for (const container of containers) {
      containerMap.set(container.service, container)
    }

    // Merge services with status and env values
    return services.map((service) => {
      // Update env vars with actual values from .env
      const enrichedEnvVars = service.envVars.map((ev) => ({
        ...ev,
        value: envValues[ev.name] ?? ev.value,
      }))

      // Also update port descriptions with actual values
      const enrichedPorts = service.ports.map((port) => {
        if (port.description && envValues[port.description]) {
          return {
            ...port,
            host: parseInt(envValues[port.description], 10) || port.host,
          }
        }
        return port
      })

      const firstPort = enrichedPorts[0]
      const url = firstPort ? `http://localhost:${firstPort.host}` : undefined

      return {
        ...service,
        ports: enrichedPorts,
        envVars: enrichedEnvVars,
        url,
        containerStatus: containerMap.get(service.name) || null,
      }
    })
  },
)

/**
 * Find container ID by service name
 */
async function findContainerByService(
  serviceName: string,
): Promise<string | null> {
  try {
    const { stdout } = await execAsync(
      `docker ps -a --filter "label=com.docker.compose.service=${serviceName}" --format "{{.ID}}"`,
    )
    const containerId = stdout.trim().split('\n')[0]
    return containerId || null
  } catch {
    return null
  }
}

/**
 * Start a service
 */
export const startService = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: string) => input)
  .handler(
    async ({
      data: serviceName,
    }): Promise<{ success: boolean; error?: string }> => {
      try {
        const containerId = await findContainerByService(serviceName)
        if (!containerId) {
          return {
            success: false,
            error: `No container found for service: ${serviceName}`,
          }
        }

        await execAsync(`docker start ${containerId}`, {
          timeout: 60000,
        })

        return { success: true }
      } catch (error) {
        return {
          success: false,
          error:
            error instanceof Error ? error.message : 'Failed to start service',
        }
      }
    },
  )

/**
 * Stop a service
 */
export const stopService = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: string) => input)
  .handler(
    async ({
      data: serviceName,
    }): Promise<{ success: boolean; error?: string }> => {
      try {
        const containerId = await findContainerByService(serviceName)
        if (!containerId) {
          return {
            success: false,
            error: `No container found for service: ${serviceName}`,
          }
        }

        await execAsync(`docker stop ${containerId}`, {
          timeout: 30000,
        })

        return { success: true }
      } catch (error) {
        return {
          success: false,
          error:
            error instanceof Error ? error.message : 'Failed to stop service',
        }
      }
    },
  )

/**
 * Restart a service
 */
export const restartService = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: string) => input)
  .handler(
    async ({
      data: serviceName,
    }): Promise<{ success: boolean; error?: string }> => {
      try {
        const containerId = await findContainerByService(serviceName)
        if (!containerId) {
          return {
            success: false,
            error: `No container found for service: ${serviceName}`,
          }
        }

        await execAsync(`docker restart ${containerId}`, {
          timeout: 60000,
        })

        return { success: true }
      } catch (error) {
        return {
          success: false,
          error:
            error instanceof Error
              ? error.message
              : 'Failed to restart service',
        }
      }
    },
  )
