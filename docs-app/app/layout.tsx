import "./global.css";
import type { Metadata } from "next";
import { Provider } from "@/components/provider";
import { appName } from "@/lib/shared";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3101"),
  title: {
    default: appName,
    template: `%s | ${appName}`,
  },
};

export default function Layout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="flex min-h-screen flex-col">
        <Provider>{children}</Provider>
      </body>
    </html>
  );
}
