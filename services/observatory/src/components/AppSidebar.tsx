import { useNavigate, useRouterState } from '@tanstack/react-router'
import {
  Boxes,
  Database,
  GitBranch,
  LayoutDashboard,
  Shield,
  Table,
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
  SidebarSeparator,
} from '@/components/ui/sidebar'

type NavItem = {
  to: '/' | '/hub' | '/data' | '/assets' | '/graph' | '/branches' | '/quality'
  label: string
  icon: ReactNode
}

const navItems: Array<NavItem> = [
  { to: '/', label: 'Dashboard', icon: <LayoutDashboard /> },
  { to: '/hub', label: 'Hub', icon: <Boxes /> },
  { to: '/data', label: 'Data Explorer', icon: <Table /> },
  { to: '/assets', label: 'Assets', icon: <Database /> },
  { to: '/graph', label: 'Lineage Graph', icon: <GitBranch /> },
  { to: '/branches', label: 'Branches', icon: <GitBranch /> },
  { to: '/quality', label: 'Quality', icon: <Shield /> },
]

export function AppSidebar() {
  const navigate = useNavigate()
  const pathname = useRouterState({
    select: (state) => state.location.pathname,
  })

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <div className="px-2 py-1 text-xs text-muted-foreground">Phlo</div>
        <div className="px-2 text-sm font-semibold tracking-tight">
          Observatory
        </div>
      </SidebarHeader>

      <SidebarSeparator />

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
