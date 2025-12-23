/**
 * Services Server Functions
 *
 * Server-side functions for service discovery and Docker management.
 * Reads service.yaml files and interacts with Docker Compose.
 */

import { createServerFn } from '@tanstack/react-start'
import { exec } from 'node:child_process'
import { existsSync } from 'node:fs'
import { readFile, readdir } from 'node:fs/promises'
import { join } from 'node:path'
import { promisify } from 'node:util'

import { authMiddleware } from '@/server/auth.server'
import { parse as parseYaml } from 'yaml'

const execAsync = promisify(exec)
const phloCommand = process.env.PHLO_CLI_COMMAND ?? 'uv run phlo'
const phloProjectPath = process.env.PHLO_PROJECT_PATH
const envFilePath = process.env.ENV_FILE_PATH

const serviceMetadata: Record<
  string,
  { category: string; description: string; default: boolean }
> = {
  postgres: {
    category: 'core',
    description: 'PostgreSQL metadata and catalog store',
    default: true,
  },
  minio: {
    category: 'core',
    description: 'S3-compatible object storage',
    default: true,
  },
  'minio-setup': {
    category: 'core',
    description: 'Initializes MinIO buckets and policies',
    default: true,
  },
  nessie: {
    category: 'core',
    description: 'Git-like catalog for Iceberg tables',
    default: true,
  },
  trino: {
    category: 'core',
    description: 'Distributed SQL query engine',
    default: true,
  },
  'dagster-webserver': {
    category: 'orchestration',
    description: 'Dagster UI and GraphQL API',
    default: true,
  },
  'dagster-daemon': {
    category: 'orchestration',
    description: 'Dagster daemon for schedules and sensors',
    default: true,
  },
  observatory: {
    category: 'orchestration',
    description: 'Phlo Observatory UI',
    default: true,
  },
  pgweb: {
    category: 'admin',
    description: 'PostgreSQL web client',
    default: false,
  },
  superset: {
    category: 'bi',
    description: 'BI dashboards and exploration',
    default: false,
  },
  postgrest: {
    category: 'api',
    description: 'REST API for PostgreSQL',
    default: false,
  },
  hasura: {
    category: 'api',
    description: 'GraphQL API for PostgreSQL',
    default: false,
  },
  fastapi: {
    category: 'api',
    description: 'Custom FastAPI service layer',
    default: false,
  },
  prometheus: {
    category: 'observability',
    description: 'Metrics collection and scraping',
    default: false,
  },
  grafana: {
    category: 'observability',
    description: 'Dashboards and monitoring UI',
    default: false,
  },
  loki: {
    category: 'observability',
    description: 'Log aggregation',
    default: false,
  },
  alloy: {
    category: 'observability',
    description: 'Metrics and log agent',
    default: false,
  },
}

interface CliServiceDefinition {
  name: string
  description?: string
  category?: string
  default?: boolean
  profile?: string | null
  depends_on?: Array<string>
  compose?: {
    ports?: Array<string>
  }
  env_vars?: Record<
    string,
    {
      default?: string | number
      description?: string
      secret?: boolean
    }
  >
}

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

interface NativeProcessEntry {
  pid: number
  started_at?: number
  log?: string
}

function isPidRunning(pid: number): boolean {
  try {
    process.kill(pid, 0)
    return true
  } catch {
    return false
  }
}

async function loadNativeProcesses(): Promise<
  Record<string, NativeProcessEntry>
> {
  const root = phloProjectPath ?? process.cwd()
  const statePath = join(root, '.phlo', 'native-processes.json')
  try {
    const raw = await readFile(statePath, 'utf-8')
    return JSON.parse(raw) as Record<string, NativeProcessEntry>
  } catch {
    return {}
  }
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
  if (envFilePath) {
    return envFilePath
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

function buildServiceDefinition(
  data: CliServiceDefinition,
): ServiceDefinition | null {
  if (!data.name) {
    return null
  }

  const ports: Array<{
    host: number
    container: number
    description?: string
  }> = []
  if (data.compose?.ports) {
    for (const portMapping of data.compose.ports) {
      const match = portMapping.match(
        /\$\{([^:}]+):-?(\d+)\}:(\d+)|(\d+):(\d+)/,
      )
      if (match) {
        if (match[1]) {
          ports.push({
            host: parseInt(match[2], 10),
            container: parseInt(match[3], 10),
            description: match[1],
          })
        } else {
          ports.push({
            host: parseInt(match[4], 10),
            container: parseInt(match[5], 10),
          })
        }
      }
    }
  }

  const envVars: Array<EnvVar> = []
  if (data.env_vars) {
    for (const [varName, config] of Object.entries(data.env_vars)) {
      envVars.push({
        name: varName,
        value: String(config.default ?? ''),
        description: config.description,
        secret: config.secret ?? false,
      })
    }
  }

  const firstPort = ports[0]
  const url = firstPort ? `http://localhost:${firstPort.host}` : undefined

  return {
    name: data.name,
    description: data.description || '',
    category: data.category || 'core',
    default: data.default ?? false,
    dependsOn: data.depends_on || [],
    ports,
    envVars,
    url,
  }
}

async function parseServiceYaml(
  filePath: string,
): Promise<ServiceDefinition | null> {
  try {
    const content = await readFile(filePath, 'utf-8')
    const data = parseYaml(content)
    return buildServiceDefinition(data)
  } catch {
    return null
  }
}

/**
 * Discover all services from service.yaml files
 */
async function discoverServices(): Promise<Array<ServiceDefinition>> {
  const cliServices = await discoverServicesFromCli()
  if (cliServices.length > 0) {
    return cliServices
  }

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

async function discoverServicesFromContainers(): Promise<
  Array<ServiceDefinition>
> {
  try {
    const { stdout } = await execAsync('docker ps -a --format json')
    const services: Array<ServiceDefinition> = []
    const seen = new Set<string>()

    for (const line of stdout.trim().split('\n')) {
      if (!line) continue
      const container = JSON.parse(line) as {
        Labels?: string
        Ports?: string
      }

      const labels = container.Labels || ''
      const serviceMatch = labels.match(/com\.docker\.compose\.service=([^,]+)/)
      const serviceName = serviceMatch ? serviceMatch[1] : ''
      if (!serviceName || seen.has(serviceName)) {
        continue
      }
      seen.add(serviceName)

      const ports = parsePorts(container.Ports)
      const firstPort = ports[0]
      const metadata = serviceMetadata[serviceName]

      services.push({
        name: serviceName,
        description: metadata?.description ?? '',
        category: metadata?.category ?? 'core',
        default: metadata?.default ?? false,
        dependsOn: [],
        ports,
        envVars: [],
        url: firstPort ? `http://localhost:${firstPort.host}` : undefined,
      })
    }

    return services
  } catch {
    return []
  }
}

function parsePorts(
  portsRaw?: string,
): Array<{ host: number; container: number; description?: string }> {
  if (!portsRaw) {
    return []
  }

  const ports: Array<{
    host: number
    container: number
    description?: string
  }> = []
  for (const entry of portsRaw.split(',')) {
    const match = entry.match(/:(\d+)->(\d+)/)
    if (!match) {
      continue
    }
    ports.push({
      host: parseInt(match[1], 10),
      container: parseInt(match[2], 10),
    })
  }
  return ports
}

async function discoverServicesFromCli(): Promise<Array<ServiceDefinition>> {
  try {
    const execOptions = phloProjectPath ? { cwd: phloProjectPath } : undefined
    const { stdout } = await execAsync(
      `${phloCommand} services list --json`,
      execOptions,
    )
    const parsed = JSON.parse(stdout) as Array<CliServiceDefinition>
    return parsed
      .map((service) => buildServiceDefinition(service))
      .filter((service): service is ServiceDefinition => Boolean(service))
  } catch {
    return discoverServicesFromContainers()
  }
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
    const [services, containers, envValues, nativeProcesses] =
      await Promise.all([
        discoverServices(),
        getDockerStatus(),
        loadEnvValues(),
        loadNativeProcesses(),
      ])

    // Create a map of service name to container status
    const containerMap = new Map<string, DockerContainerStatus>()
    for (const container of containers) {
      containerMap.set(container.service, container)
    }

    // Merge services with status and env values
    return (
      services
        // Hide one-shot init containers from the Hub (they run once and exit successfully).
        .filter((service) => service.name !== 'minio-setup')
        .map((service) => {
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
          const url = firstPort
            ? `http://localhost:${firstPort.host}`
            : undefined

          const dockerStatus = containerMap.get(service.name) || null
          const native = nativeProcesses[service.name]
          const nativeStatus: DockerContainerStatus | null =
            native && isPidRunning(native.pid)
              ? {
                  name: `native:${service.name}`,
                  service: service.name,
                  status: 'running',
                  health: 'native',
                  ports: undefined,
                }
              : null

          return {
            ...service,
            ports: enrichedPorts,
            envVars: enrichedEnvVars,
            url,
            containerStatus: nativeStatus ?? dockerStatus,
          }
        })
    )
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
  .inputValidator((input: { serviceName: string }) => input)
  .handler(
    async ({
      data: { serviceName },
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
  .inputValidator((input: { serviceName: string }) => input)
  .handler(
    async ({
      data: { serviceName },
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
  .inputValidator((input: { serviceName: string }) => input)
  .handler(
    async ({
      data: { serviceName },
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
