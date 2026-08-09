import { Playfair_Display } from "next/font/google";
import SmoothScroll from "./components/SmoothScroll";
import "./globals.css";

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-serif",
  weight: ["400", "500", "600", "700"],
});

export const metadata = {
  title: "CheapHouse Japan — Verify Before You Buy",
  description:
    "Verify whether a Japanese property is available, workable, and worth pursuing before you spend on travel or due diligence.",
  keywords: ["akiya", "Japan property", "listing verification", "Japanese real estate"],
  openGraph: {
    title: "CheapHouse Japan — Verify Before You Buy",
    description: "Availability first. Evidence before certainty.",
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
