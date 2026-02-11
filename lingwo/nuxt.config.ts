// https://nuxt.com/docs/api/configuration/nuxt-config
import { defineNuxtConfig } from "nuxt/config";
import tailwindcss from "@tailwindcss/vite";

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  css: ['./assets/css/main.css'],
  alias: {
    '@': './',
    '@/': './',
  },
  vite: {
    plugins: [
      tailwindcss(),
    ],
    resolve: {
      alias: {
        '@': './.',
        '@/': './',
      },
    },
  },
  app: {
    pageTransition: { name: 'page', mode: 'out-in' }
  },
  modules: ['@pinia/nuxt', 'nuxt-lucide-icons', 'shadcn-nuxt', [
    '@nuxtjs/google-fonts',
    {
      families: {
        Inter: '200..700'
      },
      display: 'swap'
    }
  ], '@sidebase/nuxt-auth', 'pinia-plugin-persistedstate/nuxt', '@nuxt/image'],
  auth: {
    baseURL: process.env.NUXT_PUBLIC_BASE_AUTH,
    originEnvKey: 'NUXT_PUBLIC_BASE_AUTH',
    trustHost: true,
    provider: {
      type: 'authjs',
      trustHost: true,
      defaultProvider: 'credentials',
      addDefaultCallbackUrl: false
    }
  },
  shadcn: {
    prefix: '',
    componentDir: './components/ui'
  },
  
  runtimeConfig: {
    authUrl: process.env.NUXT_AUTH_URL,
    backendService: process.env.NUXT_BACKEND_SERVICE,
    baseURL: process.env.NUXT_PUBLIC_BASE_URL,
    public: {
      baseURL: process.env.NUXT_PUBLIC_BASE_URL,
      baseApiURL: process.env.NUXT_PUBLIC_BASE_API_URL,
      domain: process.env.NUXT_PUBLIC_DOMAIN,
      full_domain: process.env.NUXT_PUBLIC_FULL_DOMAIN,
    },
  },
})