import { renderMermaidSVG } from "beautiful-mermaid";

type MermaidProps = {
  chart: string;
};

export function Mermaid({ chart }: MermaidProps) {
  try {
    const svg = renderMermaidSVG(chart, {
      bg: "var(--color-fd-card)",
      fg: "var(--color-fd-foreground)",
      accent: "var(--color-fd-primary)",
      border: "var(--color-fd-border)",
      line: "var(--color-fd-foreground)",
      muted: "var(--color-fd-muted-foreground)",
      surface: "var(--color-fd-secondary)",
      padding: 24,
      nodeSpacing: 16,
      layerSpacing: 28,
      componentSpacing: 16,
      transparent: true,
    }).replace("<svg ", '<svg class="phlo-mermaid-svg" ');

    return (
      <div
        className="phlo-mermaid overflow-x-auto rounded-xl border bg-fd-card p-4"
        dangerouslySetInnerHTML={{ __html: svg }}
      />
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);

    return (
      <pre className="overflow-x-auto rounded-xl border bg-fd-card p-4 text-sm">
        <code>{message}</code>
      </pre>
    );
  }
}
