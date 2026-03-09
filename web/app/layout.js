import { Playfair_Display } from "next/font/google";
import SmoothScroll from "./components/SmoothScroll";
import "./globals.css";

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-serif",
  weight: ["400", "500", "600", "700"],
});

export const metadata = {
  title: "CheapHouse — Find Dream Homes Around the World",
  description:
    "The decision platform for international home buyers. Discover, compare, and decide on affordable homes worldwide.",
  keywords: ["real estate", "cheap houses", "akiya", "Japan", "affordable homes", "international property"],
  openGraph: {
    title: "CheapHouse — Find Dream Homes Around the World",
    description: "The decision platform for international buyers. Discover affordable homes worldwide.",
    type: "website",
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={playfair.variable} suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('ch-theme');if(t)document.documentElement.setAttribute('data-theme',t)}catch(e){}})()`,
          }}
        />
      </head>
      <body>
        <SmoothScroll>{children}</SmoothScroll>
      </body>
    </html>
  );
}
