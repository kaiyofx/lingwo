/**
 * При 401 от бэкенда (истёкший/невалидный токен) — выходим из аккаунта и редирект на /login.
 * Патчим globalThis.$fetch, т.к. в компонентах используется именно он (auto-import), а не nuxtApp.$fetch.
 */
export default defineNuxtPlugin({
  name: 'api-401-logout',
  enforce: 'post', // после auth и инициализации $fetch
  setup(nuxtApp) {
    const config = useRuntimeConfig()
    const baseApiURL = (config.public.baseApiURL as string) || ''

    const originalFetch = globalThis.$fetch as typeof $fetch & { raw?: typeof $fetch.raw; create?: typeof $fetch.create; native?: typeof fetch }
    if (!originalFetch) return

    const wrapped = async (request: unknown, options?: unknown) => {
      try {
        return await originalFetch(request as any, options as any)
      } catch (err: any) {
        const status = err?.status ?? err?.statusCode ?? err?.response?.status
        if (status === 401 && baseApiURL) {
          const urlStr =
            typeof request === 'string'
              ? request
              : (request as Request)?.url ?? (err?.request as Request)?.url ?? ''
          if (urlStr.startsWith(baseApiURL)) {
            const { signOut } = useAuth()
            await signOut({ callbackUrl: '/login' })
            await navigateTo('/login')
          }
        }
        throw err
      }
    }
    Object.assign(wrapped, {
      raw: originalFetch.raw,
      create: originalFetch.create,
      ...(originalFetch.native && { native: originalFetch.native }),
    })

    ;(globalThis as any).$fetch = wrapped
    ;(nuxtApp as any).$fetch = wrapped
  },
})
