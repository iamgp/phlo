import Link from "next/link";

export default function HomePage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center text-center">
      <h1 className="mb-4 text-2xl font-bold">Phlo Documentation</h1>
      <p>
        Open{" "}
        <Link href="/docs" className="font-medium underline">
          /docs
        </Link>{" "}
        to browse the documentation.
      </p>
      <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Link
            href="/docs"
            className="rounded-md border px-4 py-2 text-sm font-medium"
          >
            Open Docs
          </Link>
          <Link
            href="/docs/getting-started/installation"
            className="rounded-md border px-4 py-2 text-sm font-medium"
          >
            Installation
          </Link>
      </div>
    </main>
  );
}
