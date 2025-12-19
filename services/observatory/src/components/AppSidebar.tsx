import { useNavigate, useRouterState } from '@tanstack/react-router'
import {
  Boxes,
  Database,
  GitBranch,
  LayoutDashboard,
  Settings,
  Shield,
  Table,
  Terminal,
} from 'lucide-react'
import type { ReactNode } from 'react'

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar'

type NavItem = {
  to:
    | '/'
    | '/hub'
    | '/data'
    | '/sql'
    | '/assets'
    | '/graph'
    | '/branches'
    | '/quality'
    | '/settings'
  label: string
  icon: ReactNode
}

const navItems: Array<NavItem> = [
  { to: '/', label: 'Dashboard', icon: <LayoutDashboard /> },
  { to: '/hub', label: 'Hub', icon: <Boxes /> },
  { to: '/data', label: 'Data Explorer', icon: <Table /> },
  { to: '/sql', label: 'SQL Query', icon: <Terminal /> },
  { to: '/assets', label: 'Assets', icon: <Database /> },
  { to: '/graph', label: 'Lineage Graph', icon: <GitBranch /> },
  { to: '/branches', label: 'Branches', icon: <GitBranch /> },
  { to: '/quality', label: 'Quality', icon: <Shield /> },
  { to: '/settings', label: 'Settings', icon: <Settings /> },
]

export function AppSidebar() {
  const navigate = useNavigate()
  const pathname = useRouterState({
    select: (state) => state.location.pathname,
  })

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="h-14 px-4 py-0 justify-center border-b border-border">
        <div className="text-xs text-muted-foreground leading-none">Phlo</div>
        <div className="text-sm font-semibold tracking-tight leading-none">
          Observatory
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarMenu>
          {navItems.map((item) => (
            <SidebarMenuItem key={item.to}>
              <SidebarMenuButton
                isActive={
                  pathname === item.to || pathname.startsWith(`${item.to}/`)
                }
                tooltip={item.label}
                onClick={() => navigate({ to: item.to })}
              >
                {item.icon}
                <span>{item.label}</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarContent>

      <SidebarFooter>
        <div className="px-2 text-xs text-muted-foreground">
          Phase 4 • v0.0.4
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}
