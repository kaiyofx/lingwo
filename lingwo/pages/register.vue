<script lang="ts" setup>
import { Input } from '~/components/ui/input';
import { Button } from '~/components/ui/button'
import { NuxtLink } from '#components';
import { toast } from 'vue-sonner';

definePageMeta({
  middleware: 'guest'
});

const config = useRuntimeConfig();
const confirmStore = useConfirmationStore();
const router = useRouter();

const mail_regex : RegExp = /^(?=.{1,254}$)(?=.{1,64}@)[-!#$%&'*+/0-9=?A-Z^_`a-z{|}~]+(\.[-!#$%&'*+/0-9=?A-Z^_`a-z{|}~]+)*@[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?(\.[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*$/;
const loadingButton = ref(false);
const formRef = ref<HTMLFormElement | null>(null);

const usernameRef = ref('')
const emailRef = ref('')
const passwordRef = ref('')

const validUsername = () => {
  return usernameRef.value.length > 2 && usernameRef.value.length < 16
}

const validPassword = () => {
  return passwordRef.value.length > 5 && passwordRef.value.length < 51
}

const signUp = async() => {
  loadingButton.value = true;
  
  if (!validUsername()) {
    toast.error("Некорректный логин");
    loadingButton.value = false;
    return;
  } else if(!validPassword()) {
    toast.error("Некорректный пароль");
    loadingButton.value = false;
    return;
  } else if(!mail_regex.test(emailRef.value) || emailRef.value.trim().endsWith("@mriscan.live")) {
    toast.error("Некорректная почта");
    loadingButton.value = false;
    return;
  }

  try {
    await $fetch("/api/auth/send-otp", {
      method: 'post',
      body: {
        email: emailRef.value,
        username: usernameRef.value,
      },
      headers: {
        'Content-Type': 'application/json',
      },
      onResponseError({ response }) {
        if (response._data) {
          const message = response._data.message || response._data.statusMessage;
          toast.error('Ошибка', { description: message});
          return;
        }
      }
    },) as { message?: string };

    confirmStore.set({
      username: usernameRef.value,
      email: emailRef.value,
      password: passwordRef.value,
    })

    await router.push('/confirmation');
  } catch(e) { 
    console.error('Registration error:', e);
    return; 
  } finally {
    usernameRef.value = '';
    passwordRef.value = '';
    emailRef.value = '';
    loadingButton.value = false;
  }
}

useHead({
  title: "Регистрация - Лингво"
})
</script>

<template>
  <div class="flex items-center justify-center min-h-screen bg-linear-to-br from-white via-green-50/30 to-emerald-50/40 px-4 py-8">
    <div class="rounded-xl bg-white shadow-lg border border-green-100/50 p-6 sm:p-8 w-full max-w-md mx-auto backdrop-blur-sm">
      <!-- Logo Section -->
      <div class="mb-6 text-center">
        <div class="inline-flex items-center justify-center w-full mb-4">
          <NuxtImg width="170" src="/assets/logo.svg" alt="Lingwo"/>
        </div>
        <h1 class="text-3xl font-bold text-gray-800 mb-2">Регистрация</h1>
        <p class="text-sm text-gray-500">Создайте новый аккаунт Лингво</p>
      </div>

      <!-- Registration Form -->
      <form ref="formRef" @submit.prevent="signUp" class="space-y-4">
        <div>
          <label for="email" class="block text-sm font-medium text-gray-700 mb-1.5">
            Email
          </label>
          <Input 
            id="email"
            placeholder="Введите ваш email" 
            type="email" 
            v-model="emailRef"
            class="w-full"
          />
        </div>

        <div>
          <label for="username" class="block text-sm font-medium text-gray-700 mb-1.5">
            Логин
          </label>
          <Input 
            id="username"
            placeholder="Введите логин (3-15 символов)" 
            type="text" 
            v-model="usernameRef"
            class="w-full"
          />
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-gray-700 mb-1.5">
            Пароль
          </label>
          <Input 
            id="password"
            placeholder="Введите пароль (минимум 6 символов)" 
            type="password" 
            v-model="passwordRef"
            class="w-full"
          />
        </div>

        <!-- Submit Button -->
        <div class="pt-2">
          <Button 
            v-if="!loadingButton"
            :disabled="!(validUsername() && validPassword() && mail_regex.test(emailRef))"
            type="submit"
            class="w-full h-11 text-base font-semibold shadow-md hover:shadow-lg transition-all"
            variant="default"
          >
            Продолжить
          </Button>
          <div v-else class="flex justify-center py-2">
            <div class="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          </div>
        </div>
      </form>

      <!-- Login Link -->
      <div class="mt-6 text-center">
        <p class="text-sm text-gray-600">
          Уже есть аккаунт?
          <NuxtLink 
            class="text-primary hover:text-primary/80 font-semibold ml-1 transition-colors" 
            href="/login"
          >
            Войти
          </NuxtLink>
        </p>
      </div>

      <!-- Additional Info -->
      <!-- <div class="mt-6 pt-6 border-t border-gray-100">
        <p class="text-xs text-center text-gray-500">
          Регистрируясь, вы соглашаетесь с нашими<br/>
          <a href="#" class="text-primary hover:underline">Условиями использования</a> и 
          <a href="#" class="text-primary hover:underline">Политикой конфиденциальности</a>
        </p>
      </div> -->
    </div>
  </div>
</template>

<style scoped>
/* Custom animations */
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Responsive adjustments for very small screens */
@media (max-width: 375px) {
  .rounded-xl {
    border-radius: 0.75rem;
  }
}
</style>
