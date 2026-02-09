interface AuthServiceResponse {
  success: boolean;
  message?: string;
}

export default defineEventHandler(async (event: any) => {
  const body = await readBody(event)
  const { email, username } = body

  // Validate input
  if (!email || !username) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Email и username обязательны'
    })
  }

  const config = useRuntimeConfig()
  const authBaseURL = config.authUrl

  if (!authBaseURL) {
    throw createError({
      statusCode: 500,
      statusMessage: 'AUTH_URL не задан в окружении'
    })
  }

  console.log('Sending OTP to:', email, 'for user:', username)
  console.log('Auth service URL:', authBaseURL)

  try {
    const otpResponse = await $fetch<AuthServiceResponse>('/api/v1/otp/send/', {
      baseURL: authBaseURL,
      method: 'POST',
      body: JSON.stringify({
        email,
        username,
        auth_type: 2 // signup
      }),
      headers: {
        'Content-Type': 'application/json',
      }
    })

    return {
      success: true,
      data: otpResponse
    }

  } catch (error: any) {
    console.error('Send OTP error:', error)
    console.error('Error data:', error.data)
    console.error('Error response:', error.response)
    console.error('Error message:', error.message)
    
    // Handle different error types
    let errorMessage = 'Произошла ошибка при отправке кода';
    
    if (error.data) {
      // Django/API errors
      if (error.data.email && Array.isArray(error.data.email)) {
        errorMessage = error.data.email[0];
      } else if (error.data.username && Array.isArray(error.data.username)) {
        errorMessage = error.data.username[0];
      } else if (error.data.error) {
        errorMessage = error.data.error;
      } else if (error.data.detail) {
        errorMessage = error.data.detail;
      } else if (typeof error.data === 'string') {
        errorMessage = error.data;
      }
    } else if (error.message) {
      // Network or other errors
      if (error.message.includes('fetch failed') || error.message.includes('ECONNREFUSED')) {
        errorMessage = 'Сервис авторизации недоступен. Проверьте подключение.';
      } else {
        errorMessage = error.message;
      }
    }
    
    throw createError({
      statusCode: error.statusCode || 400,
      statusMessage: errorMessage,
      data: error.data,
    })
  }
})
