<script setup lang="ts">
import { Input } from '~/components/ui/input';
import { Button } from '~/components/ui/button';
import { toast } from 'vue-sonner';

definePageMeta({
  middleware: 'guest'
});

const confirmStore = useConfirmationStore();
const router = useRouter();

const otpCode = ref(['', '', '', '', '', '']);
const loadingButton = ref(false);
const resendTimer = ref(60);
const canResend = ref(false);
let timerInterval: ReturnType<typeof setInterval> | null = null;

// Start resend timer
const startResendTimer = () => {
  canResend.value = false;
  resendTimer.value = 60;
  
  timerInterval = setInterval(() => {
    resendTimer.value--;
    
    if (resendTimer.value <= 0) {
      canResend.value = true;
      if (timerInterval) {
        clearInterval(timerInterval);
      }
    }
  }, 1000);
};

// Redirect if no confirmation data
onMounted(() => {
  if (!confirmStore.confirm.email || !confirmStore.confirm.username) {
    toast.error('Ошибка', {
      description: 'Данные регистрации не найдены'
    });
    router.push('/register');
  } else {
    // Start timer when component mounts
    startResendTimer();
  }
});

// Clear timer on unmount
onUnmounted(() => {
  if (timerInterval) {
    clearInterval(timerInterval);
  }
});

const handleInput = (index: number, event: Event) => {
  const target = event.target as HTMLInputElement;
  const value = target.value;
  
  // Only allow numbers
  if (!/^\d*$/.test(value)) {
    target.value = otpCode.value[index];
    return;
  }
  
  otpCode.value[index] = value.slice(-1);
  
  // Auto-focus next input
  if (value && index < 5) {
    const nextInput = target.parentElement?.nextElementSibling?.querySelector('input');
    nextInput?.focus();
  }
};

const handleKeyDown = (index: number, event: KeyboardEvent) => {
  // Handle backspace
  if (event.key === 'Backspace' && !otpCode.value[index] && index > 0) {
    const prevInput = (event.target as HTMLInputElement).parentElement?.previousElementSibling?.querySelector('input');
    prevInput?.focus();
  }
};

const handlePaste = (event: ClipboardEvent) => {
  event.preventDefault();
  const pastedData = event.clipboardData?.getData('text').slice(0, 6);
  
  if (pastedData && /^\d+$/.test(pastedData)) {
    const digits = pastedData.split('');
    digits.forEach((digit, index) => {
      if (index < 6) {
        otpCode.value[index] = digit;
      }
    });
  }
};

const confirmRegistration = async () => {
  const code = otpCode.value.join('');
  
  if (code.length !== 6) {
    toast.error('Ошибка', {
      description: 'Введите 6-значный код'
    });
    return;
  }
  
  loadingButton.value = true;
  
  try {
    // TODO: Replace with actual API call
    await $fetch('/api/auth/verify-otp', {
      method: 'POST',
      body: {
        email: confirmStore.confirm.email,
        username: confirmStore.confirm.username,
        password: confirmStore.confirm.password,
        code: code
      }
    });
    
    toast.success('Успех', {
      description: 'Регистрация завершена!'
    });
    
    confirmStore.clear();
    await router.push('/login');
    
  } catch (error: any) {
    console.error('Confirmation error:', error);
    toast.error('Ошибка', {
      description: error.data?.message || 'Неверный код подтверждения'
    });
    otpCode.value = ['', '', '', '', '', ''];
  } finally {
    loadingButton.value = false;
  }
};

const resendCode = async () => {
  if (!canResend.value) return;
  
  try {
    await $fetch('/api/auth/send-otp', {
      method: 'POST',
      body: {
        email: confirmStore.confirm.email,
        username: confirmStore.confirm.username,
      }
    });
    
    toast.success('Успех', {
      description: 'Код отправлен повторно'
    });
    
    // Restart timer after successful resend
    startResendTimer();
  } catch (error: any) {
    toast.error('Ошибка', {
      description: error.data?.statusMessage || 'Не удалось отправить код повторно'
    });
  }
};

useHead({
  title: 'Подтверждение - Лингво'
});
</script>

<template>
  <div class="flex items-center justify-center min-h-screen bg-linear-to-br from-white via-green-50/30 to-emerald-50/40 px-4 py-8">
    <div class="rounded-xl bg-white shadow-lg border border-green-100/50 p-6 sm:p-8 w-full max-w-md mx-auto backdrop-blur-sm">
      <!-- Logo Section -->
      <div class="mb-6 text-center">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-linear-to-br from-primary to-emerald-400 mb-4 shadow-md">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>
        <h1 class="text-3xl font-bold text-gray-800 mb-2">Подтверждение</h1>
        <p class="text-sm text-gray-500">
          Мы отправили код на<br/>
          <span class="font-semibold text-primary">{{ confirmStore.confirm.email }}</span>
        </p>
      </div>

      <!-- OTP Input -->
      <form @submit.prevent="confirmRegistration" class="space-y-6">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-3 text-center">
            Введите код подтверждения
          </label>
          <div class="flex justify-center gap-2 sm:gap-3">
            <div v-for="(digit, index) in otpCode" :key="index" class="w-12 h-14 sm:w-14 sm:h-16">
              <input
                :value="digit"
                @input="handleInput(index, $event)"
                @keydown="handleKeyDown(index, $event)"
                @paste.prevent="handlePaste"
                type="text"
                inputmode="numeric"
                maxlength="1"
                class="w-full h-full text-center text-2xl font-bold border-2 border-gray-300 rounded-lg focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all"
                :class="{ 'border-primary': digit }"
              />
            </div>
          </div>
        </div>

        <!-- Submit Button -->
        <div class="pt-2">
          <Button 
            v-if="!loadingButton"
            type="submit"
            class="w-full h-11 text-base font-semibold shadow-md hover:shadow-lg transition-all"
            variant="default"
          >
            Подтвердить
          </Button>
          <div v-else class="flex justify-center py-2">
            <div class="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          </div>
        </div>
      </form>

      <!-- Resend Code -->
      <div class="mt-6 text-center">
        <p class="text-sm text-gray-600 mb-2">
          Не получили код?
        </p>
        <button 
          @click="resendCode"
          type="button"
          :disabled="!canResend"
          class="font-semibold text-sm transition-colors"
          :class="canResend 
            ? 'text-primary hover:text-primary/80 underline cursor-pointer' 
            : 'text-gray-400 cursor-not-allowed'"
        >
          <span v-if="canResend">Отправить повторно</span>
          <span v-else>Повторная отправка через {{ resendTimer }}с</span>
        </button>
      </div>

      <!-- Back to Register -->
      <div class="mt-6 pt-6 border-t border-gray-100 text-center">
        <NuxtLink 
          to="/register"
          class="text-sm text-gray-600 hover:text-gray-800 transition-colors"
        >
          ← Вернуться к регистрации
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

input[type=number] {
  -moz-appearance: textfield;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
