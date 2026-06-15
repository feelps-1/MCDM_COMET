import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "COMET DSS",
  description: "Sistema de apoio a decisao com metodo COMET"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
