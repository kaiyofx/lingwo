export default defineNuxtRouteMiddleware(async (to, from) => {
  const { status } = useAuth()
  
  // Если пользователь авторизован, редиректим на главную
  if (status.value === 'authenticated') {
    return navigateTo('/')
  }
})
