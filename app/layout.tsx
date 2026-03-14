import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DDR Report Generator",
  description: "Generate Detailed Diagnostic Reports from Inspection and Thermal Image PDFs",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

