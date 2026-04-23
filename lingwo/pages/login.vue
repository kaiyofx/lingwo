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
const runtimeConfig = useRuntimeConfig();

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
const telegramLoading = ref(false);
const telegramWidgetError = ref('');
const telegramWidgetContainer = ref<HTMLDivElement | null>(null);
const telegramBotUsername = computed(() => runtimeConfig.public.telegramBotUsername || 'lingwobot');

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

interface TelegramWidgetUser {
  id: number;
  first_name?: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
  auth_date: number;
  hash: string;
}

const handleTelegramSignIn = async (user: TelegramWidgetUser) => {
  telegramLoading.value = true;
  try {
    const result = await signIn('credentials', {
      telegramAuth: JSON.stringify(user),
      rememberMe: rememberMeRef.value.toString(),
      redirect: false
    });

    if (result?.error) {
      toast.error("Ошибка", {
        description: "Не удалось авторизоваться через Telegram"
      });
      return;
    }

    toast.success("Успех", {
      description: "Вход через Telegram выполнен"
    });
    await router.push('/');
  } catch (error) {
    console.error("Ошибка Telegram авторизации:", error);
    toast.error("Ошибка", {
      description: "Произошла ошибка при входе через Telegram"
    });
  } finally {
    telegramLoading.value = false;
  }
};

const mountTelegramWidget = () => {
  if (!process.client || !telegramWidgetContainer.value) {
    return;
  }

  telegramWidgetError.value = '';
  telegramWidgetContainer.value.innerHTML = '';
  const script = document.createElement('script');
  script.async = true;
  script.src = 'https://telegram.org/js/telegram-widget.js?23';
  script.setAttribute('data-telegram-login', telegramBotUsername.value);
  script.setAttribute('data-size', 'large');
  script.setAttribute('data-onauth', 'onTelegramAuth(user)');
  script.setAttribute('data-request-access', 'write');
  script.onerror = () => {
    telegramWidgetError.value = 'Не удалось загрузить Telegram Widget. Проверьте блокировщик рекламы, CSP и доступ к telegram.org.';
  };
  script.onload = () => {
    setTimeout(() => {
      const root = telegramWidgetContainer.value;
      const widgetRendered = !!root?.querySelector('iframe, div[id^="telegram-login-"], script + *');
      if (!widgetRendered) {
        telegramWidgetError.value =
          'Telegram Widget не отрисовался. Частая причина: домен не привязан в BotFather (/setdomain) или используется неподдерживаемый домен.';
      }
    }, 1200);
  };
  telegramWidgetContainer.value.appendChild(script);
};

onMounted(() => {
  if (!process.client) {
    return;
  }
  (window as any).onTelegramAuth = (user: TelegramWidgetUser) => {
    handleTelegramSignIn(user);
  };
  mountTelegramWidget();
});

onBeforeUnmount(() => {
  if (!process.client) {
    return;
  }
  delete (window as any).onTelegramAuth;
});

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

      <div class="my-6 flex items-center">
        <div class="h-px flex-1 bg-gray-200"></div>
        <span class="px-3 text-xs text-gray-500 uppercase">или</span>
        <div class="h-px flex-1 bg-gray-200"></div>
      </div>

      <div class="space-y-2">
        <p class="text-center text-sm text-gray-600">Войти через Telegram</p>
        <div ref="telegramWidgetContainer" class="flex justify-center min-h-10"></div>
        <p v-if="telegramWidgetError" class="text-xs text-red-500 text-center">
          {{ telegramWidgetError }}
        </p>
        <div v-if="telegramLoading" class="flex justify-center py-1">
          <div class="w-6 h-6 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
        </div>
      </div>

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
