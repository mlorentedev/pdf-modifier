import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: 'https://mlorentedev.github.io',
  base: '/pdf-modifier',
  integrations: [
    starlight({
      title: 'pdf-modifier',
      favicon: '/favicon.svg',
      customCss: ['./src/styles/custom.css'],
      social: [
        {
          icon: 'github',
          label: 'GitHub',
          href: 'https://github.com/mlorentedev/pdf-modifier',
        },
      ],
      head: [
        {
          tag: 'meta',
          attrs: {
            property: 'og:title',
            content: 'pdf-modifier',
          },
        },
        {
          tag: 'meta',
          attrs: {
            property: 'og:description',
            content:
              'Find and replace text in PDFs while preserving font styles. CLI for humans, MCP server for AI agents.',
          },
        },
        {
          tag: 'meta',
          attrs: {
            property: 'og:type',
            content: 'website',
          },
        },
        {
          tag: 'meta',
          attrs: {
            property: 'og:url',
            content: 'https://mlorentedev.github.io/pdf-modifier/',
          },
        },
      ],
      sidebar: [
        { label: 'Home', slug: '' },
        { label: 'Getting Started', slug: 'getting-started' },
        {
          label: 'Guides',
          items: [
            { label: 'Troubleshooting', slug: 'guides/troubleshooting' },
          ],
        },
        {
          label: 'Reference',
          items: [
            { label: 'MCP Tools', slug: 'tools' },
            { label: 'Architecture', slug: 'reference/architecture' },
          ],
        },
      ],
    }),
  ],
});
