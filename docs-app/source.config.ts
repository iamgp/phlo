import { defineConfig, defineDocs } from 'fumadocs-mdx/config'
import { remarkGfm, remarkMdxMermaid } from 'fumadocs-core/mdx-plugins'
import { metaSchema } from 'fumadocs-core/source/schema'
import { z } from 'zod'

const phloPageSchema = z.object({
  title: z.string().optional(),
  description: z.string().optional(),
  icon: z.string().optional(),
  full: z.boolean().optional(),
  _openapi: z.looseObject({}).optional(),
})

export const docs = defineDocs({
  dir: 'content/docs',
  docs: {
    dynamic: true,
    schema: phloPageSchema,
    postprocess: {
      includeProcessedMarkdown: true,
    },
  },
  meta: {
    schema: metaSchema,
  },
})

export default defineConfig({
  mdxOptions: {
    remarkPlugins: [remarkGfm, remarkMdxMermaid],
  },
})
