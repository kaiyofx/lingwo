export default defineNuxtRouteMiddleware(async (to, from) => {
  const { status } = useAuth()
  
  // Если пользователь не авторизован, редиректим на страницу входа
  if (status.value === 'unauthenticated') {
    return navigateTo('/login')
  }
})
