import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "ShootSignal — Live shoot-day intelligence",
  description: "A cited, live risk brief for film crews."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
