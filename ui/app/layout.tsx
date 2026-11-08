import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Duo",
  description: "Review a pull request against what it claims to do.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
