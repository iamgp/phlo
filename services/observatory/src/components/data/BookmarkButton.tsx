/**
 * Bookmark toggle button component
 */

import { Star } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { useTableBookmarks } from '@/hooks/useBookmarks'
import { cn } from '@/lib/utils'

interface BookmarkButtonProps {
  catalog: string
  schema: string
  table: string
  className?: string
  size?: 'default' | 'sm' | 'icon-sm'
}

export function BookmarkButton({
  catalog,
  schema,
  table,
  className,
  size = 'icon-sm',
}: BookmarkButtonProps) {
  const { isTableBookmarked, toggleTableBookmark } = useTableBookmarks()
  const isBookmarked = isTableBookmarked(catalog, schema, table)

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    toggleTableBookmark(catalog, schema, table)
  }

  return (
    <Button
      variant="ghost"
      size={size}
      className={cn('shrink-0', className)}
      onClick={handleClick}
      title={isBookmarked ? 'Remove bookmark' : 'Add bookmark'}
    >
      <Star
        className={cn(
          'w-4 h-4 transition-colors',
          isBookmarked
            ? 'fill-yellow-400 text-yellow-400'
            : 'text-muted-foreground',
        )}
      />
    </Button>
  )
}

/**
 * Bookmark button for saved queries
 */
interface QueryBookmarkButtonProps {
  queryId: string
  isBookmarked: boolean
  onToggle: (queryId: string) => void
  className?: string
  size?: 'default' | 'sm' | 'icon-sm'
}

export function QueryBookmarkButton({
  queryId,
  isBookmarked,
  onToggle,
  className,
  size = 'icon-sm',
}: QueryBookmarkButtonProps) {
  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    onToggle(queryId)
  }

  return (
    <Button
      variant="ghost"
      size={size}
      className={cn('shrink-0', className)}
      onClick={handleClick}
      title={isBookmarked ? 'Remove bookmark' : 'Add bookmark'}
    >
      <Star
        className={cn(
          'w-4 h-4 transition-colors',
          isBookmarked
            ? 'fill-yellow-400 text-yellow-400'
            : 'text-muted-foreground',
        )}
      />
    </Button>
  )
}
