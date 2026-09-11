import type { Metadata } from "next";
import "bootstrap/dist/css/bootstrap.min.css";

// Иконка лежит в src/app/favicon.ico: Next сам добавит <link> с учётом basePath (A12).
export const metadata: Metadata = {
  title: "Тестовое задание Fullstack",
  description: "Тестовое задание Fullstack",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
