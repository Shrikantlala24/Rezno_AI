import type { Metadata } from 'next';
import { Inter, JetBrains_Mono, Newsreader } from 'next/font/google';
import localFont from 'next/font/local';
import './globals.css';

const inter = Inter({ subsets: ['latin'], variable: '--font-sans' });
const newsreader = Newsreader({ subsets: ['latin'], variable: '--font-serif' });
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono' });
const displayFont = localFont({
  src: '../fonts/GeistPixel-Regular-VariableFont_ELSH.ttf',
  variable: '--font-display',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Research Agent',
  description: 'Research agent prototype shell',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${newsreader.variable} ${jetbrainsMono.variable} ${displayFont.variable} font-sans antialiased`}>
        {children}
      </body>
    </html>
  );
}
