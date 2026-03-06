import { Inter, Outfit } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  weight: ["400", "500", "600", "700", "800"],
});

export const metadata = {
  title: "CheapHouse Japan — Find Your Dream Home in Japan",
  description:
    "The decision platform for international buyers. Discover, compare, and decide on affordable homes and akiya in Japan with hazard intelligence, lifestyle matching, and honest insights.",
  keywords: ["Japan", "real estate", "akiya", "cheap houses", "buy house Japan", "vacant houses"],
  openGraph: {
    title: "CheapHouse Japan — Find Your Dream Home in Japan",
    description: "The decision platform for international buyers looking for affordable homes in Japan.",
    type: "website",
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${inter.variable} ${outfit.variable}`}>
      <body>{children}</body>
    </html>
  );
}
