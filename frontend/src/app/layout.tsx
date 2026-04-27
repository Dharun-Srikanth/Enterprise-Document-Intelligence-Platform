import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DocIntell — Enterprise Document Intelligence",
  description: "Enterprise document analysis with sustainability analytics powered by AI",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="overflow-x-hidden">{children}</body>
    </html>
  );
}
