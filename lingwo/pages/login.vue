<script lang="ts" setup>
import { Input } from '~/components/ui/input';
import { Button } from '~/components/ui/button'
import { NuxtLink } from '#components';
import { toast } from 'vue-sonner';

definePageMeta({
  middleware: 'guest'
});

// Используем хук useAuth из @sidebase/nuxt-auth
const { signIn } = useAuth();
const router = useRouter();

const loginRef = ref('');
const passwordRef = ref('');
const rememberMeRef = ref(false);

const mail_regex : RegExp = /^(?=.{1,254}$)(?=.{1,64}@)[-!#$%&'*+/0-9=?A-Z^_`a-z{|}~]+(\.[-!#$%&'*+/0-9=?A-Z^_`a-z{|}~]+)*@[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?(\.[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*$/;

const validLogin = (value: string) => {
  return mail_regex.test(value) || (value.length > 2 && value.length < 16);
};

const validPassword = (password: string) => {
  return password.length > 4 && password.length < 51;
};

const loadingButton = ref(false);

const handleSignIn = async () => {
  loadingButton.value = true;

  try {
    const isEmail = mail_regex.test(loginRef.value)
    // Используем signIn из useAuth() вместо кастомного $fetch
    const result = await signIn('credentials', {
      username: isEmail ? '' : loginRef.value,
      email: isEmail ? loginRef.value : '',
      password: passwordRef.value,
      rememberMe: rememberMeRef.value.toString(),
      redirect: false
    });
    console.log(result)

    if (result?.error) {
      passwordRef.value = '';
      toast.error("Ошибка", {
        description: 'Неверный логин или пароль'
      });
      loadingButton.value = false;
      return;
    }

    // Успешная авторизация
    toast.success("Успех", {
      description: 'Вы авторизованы'
    });
    
    // Редирект на главную
    await router.push('/');
    
  } catch (error) {
    console.error('Ошибка авторизации:', error);
    toast.error("Ошибка", {
      description: 'Произошла ошибка при авторизации'
    });
  } finally {
    loadingButton.value = false;
    loginRef.value = '';
    passwordRef.value = '';
  }
};

useHead({ title: "Авторизация - Лингво" });
</script>

<template>
  <div class="flex items-center justify-center min-h-screen bg-linear-to-br from-white via-green-50/30 to-emerald-50/40 px-4">
    <div class="rounded-xl bg-white shadow-lg border border-green-100/50 p-6 sm:p-8 w-full max-w-md mx-auto backdrop-blur-sm">
      <!-- Logo Section -->
      <div class="mb-6 text-center">
        <div class="inline-flex items-center justify-center w-full mb-4">
          <NuxtImg width="170" src="/assets/logo.svg" alt="Lingwo"/>
        </div>
        
        <h1 class="text-3xl font-bold text-gray-800 mb-2">Добро пожаловать</h1>
        <p class="text-sm text-gray-500">Войдите в свой аккаунт Лингво</p>
      </div>

      <!-- Login Form -->
      <form @submit.prevent="handleSignIn" class="space-y-4">
        <div>
          <label for="login" class="block text-sm font-medium text-gray-700 mb-1.5">
            Логин или Email
          </label>
          <Input 
            id="login"
            placeholder="Введите логин или email" 
            type="text" 
            v-model="loginRef"
            class="w-full"
          />
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-gray-700 mb-1.5">
            Пароль
          </label>
          <Input 
            id="password"
            placeholder="Введите пароль" 
            type="password" 
            autocomplete="on" 
            v-model="passwordRef"
            class="w-full"
          />
        </div>
        
        <!-- Remember Me Checkbox -->
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <input 
              id="rememberMe"
              type="checkbox" 
              v-model="rememberMeRef"
              class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary focus:ring-2 focus:ring-offset-0 cursor-pointer"
            />
            <label for="rememberMe" class="ml-2 text-sm text-gray-600 cursor-pointer select-none">
              Запомнить меня
            </label>
          </div>
          <!-- Forgot Password Link (commented for now) -->
          <!-- <NuxtLink class="text-sm text-primary hover:text-primary/80 font-medium transition-colors" href="/recovery">
            Забыли пароль?
          </NuxtLink> -->
        </div>
        
        <!-- Submit Button -->
        <div class="pt-2">
          <Button 
            v-if="!loadingButton"
            :disabled="!(validLogin(loginRef) && validPassword(passwordRef))" 
            type="submit" 
            class="w-full h-11 text-base font-semibold shadow-md hover:shadow-lg transition-all"
            variant="default"
          >
            Войти
          </Button>
          <div v-else class="flex justify-center py-2">
            <div class="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          </div>
        </div>
      </form>

      <!-- Register Link -->
      <div class="mt-6 text-center">
        <p class="text-sm text-gray-600">
          Нет аккаунта?
          <NuxtLink 
            class="text-primary hover:text-primary/80 font-semibold ml-1 transition-colors" 
            href="/register"
          >
            Создать аккаунт
          </NuxtLink>
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Additional custom animations if needed */
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
