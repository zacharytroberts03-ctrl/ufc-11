import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "a.espncdn.com" },
      { protocol: "https", hostname: "upload.wikimedia.org" },
      { protocol: "https", hostname: "en.wikipedia.org" },
      { protocol: "https", hostname: "frontend-rouge-mu-86.vercel.app" },
    ],
  },
};

export default nextConfig;
