interface VerifyCodeResponse {
  message: string;
  registration_token?: string;
  expires_in_seconds?: number;
}

interface RegisterCompleteResponse {
  message?: string;
  error?: string;
}

export default defineEventHandler(async (event: any) => {
  const body = await readBody(event)
  const { email, code: otp, username, password } = body

  if (!email || !otp || !username || !password) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Не введены некоторые поля'
    })
  }

  const config = useRuntimeConfig()

  try {
    const authBaseURL = config.authUrl
    if (!authBaseURL) {
      throw createError({
        statusCode: 500,
        statusMessage: 'AUTH_URL не задан в окружении'
      })
    }

    // Step 1: Verify OTP code
    const verifyResponse = await $fetch<VerifyCodeResponse>('/api/v1/register/verify-code/', {
      baseURL: authBaseURL,
      method: 'POST',
      body: {
        email,
        otp
      },
      headers: {
        'Content-Type': 'application/json',
      }
    })

    const { registration_token } = verifyResponse;

    if (!registration_token) {
      throw createError({
        statusCode: 400,
        statusMessage: verifyResponse.message || 'Не удалось пройти регистрацию'
      })
    }

    // Step 2: Complete registration
    const completeRegister = await $fetch<RegisterCompleteResponse>('/api/v1/register/complete/', {
      baseURL: authBaseURL,
      method: 'POST',
      body: { 
        registration_token,
        username,
        password
      },
      headers: {
        'Content-Type': 'application/json',
      }
    })

    if (completeRegister.error) {
      throw createError({
        statusCode: 400,
        statusMessage: completeRegister.error
      })
    }

    return {
      success: true,
      data: completeRegister
    }

  } catch (error: any) {
    console.error('Error in register:', error.data)
        
    if(error.data?.username?.[0]) {
      return {
        success: false,
        error: error.data.username[0]
      }
    }
    
    throw createError({
      statusCode: 400,
      statusMessage: error.data?.error || 'Ошибка регистрации',
      data: error.data,
    })
  }
})
