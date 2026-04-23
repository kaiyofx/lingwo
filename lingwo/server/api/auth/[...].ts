import { NuxtAuthHandler } from "#auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { jwtDecode } from "jwt-decode";

// Константы времени
const SHORT_SESSION_MAX_AGE = 12 * 60 * 60; // 1 час для сессий без rememberMe
const LONG_SESSION_MAX_AGE = 30 * 24 * 60 * 60; // 30 дней для сессий с rememberMe
const TOKEN_REFRESH_BUFFER = 5 * 60 * 1000; // 5 минут до истечения

let refreshPromise: Promise<any> | null = null;

async function refreshAccessToken(token: any) {
  if (refreshPromise) {
    console.log("♻️ Token refresh already in progress, waiting...");
    return refreshPromise;
  }

  refreshPromise = (async () => {
    try {
      console.log("🔄 Refreshing access token...");
      console.log("Using refresh token (first 10 chars):", token.refreshToken?.substring(0, 10) + "...");
      
      // Если rememberMe = false, НЕ обновляем токен
      if (!token.rememberMe) {
        console.log("Remember me is false, skipping refresh");
        return {
          ...token,
          error: "RememberMeFalseNoRefresh"
        };
      }
      
      const response = await fetch(`${process.env.NUXT_AUTH_URL}/api/token/refresh/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh: token.refreshToken }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        
        // Если получили 401 - refresh token уже недействителен
        if (response.status === 401) {
          console.error("Refresh token is invalid or blacklisted:", errorData);
          return {
            ...token,
            error: "RefreshTokenInvalid",
          };
        }
        
        throw new Error(`Refresh failed: ${response.status} ${JSON.stringify(errorData)}`);
      }

      const refreshedTokens = await response.json();
      const decodedNewToken = jwtDecode(refreshedTokens.access) as { exp: number };

      console.log("✅ Token successfully refreshed!");
      console.log("New refresh token (first 10 chars):", refreshedTokens.refresh?.substring(0, 10) + "...");
      
      // ВАЖНО: При rotating refresh tokens сервер возвращает новый refresh token
      const newRefreshToken = refreshedTokens.refresh || token.refreshToken;

      return {
        ...token,
        accessToken: refreshedTokens.access,
        accessTokenExpires: decodedNewToken.exp * 1000,
        refreshToken: newRefreshToken,
        rememberMe: token.rememberMe,
        error: null,
      };
    } catch (error) {
      console.error("❌ Error refreshing token:", error);
      return {
        ...token,
        error: "RefreshAccessTokenError",
      };
    } finally {
      setTimeout(() => {
        refreshPromise = null;
      }, 1000);
    }
  })();

  return refreshPromise;
}

export default NuxtAuthHandler({
  secret: process.env.NEXTAUTH_SECRET,

  events: {
    async signOut(message) {
      try {
        console.log("🔒 Signing out, blacklisting refresh token...");
        await fetch(`${process.env.NUXT_AUTH_URL}/api/token/logout/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            refresh: message.token?.refreshToken,
          }),
        });
        console.log("✅ Refresh token blacklisted");
      } catch (error) {
        console.error("Logout error:", error);
      }
    }
  },

  providers: [
    // @ts-expect-error You need to use .default here for it to work during SSR
    CredentialsProvider.default({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "text" },
        username: { label: "Username", type: "text" },
        password: { label: "Password", type: "password" },
        telegramAuth: { label: "Telegram Auth", type: "text", required: false },
        rememberMe: {
          label: "Remember Me",
          type: "checkbox",
          required: false,
        },
      },

      async authorize(credentials: any) {
        try {
          const rememberMe = credentials?.rememberMe === true || 
                           credentials?.rememberMe === "true";
          const telegramAuthRaw = credentials?.telegramAuth;

          console.log(`🔐 Login attempt, rememberMe: ${rememberMe}`);

          const endpoint = telegramAuthRaw
            ? `${process.env.NUXT_AUTH_URL}/api/token/telegram/`
            : `${process.env.NUXT_AUTH_URL}/api/token/`;
          let requestBody: Record<string, unknown>;

          if (telegramAuthRaw) {
            let parsedTelegramAuth: Record<string, unknown> | null = null;
            try {
              parsedTelegramAuth =
                typeof telegramAuthRaw === "string" ? JSON.parse(telegramAuthRaw) : telegramAuthRaw;
            } catch (parseError) {
              console.error("Invalid telegramAuth payload", parseError);
              return null;
            }
            requestBody = parsedTelegramAuth ?? {};
          } else {
            requestBody = {
              user_email: credentials?.email,
              username: credentials?.username,
              password: credentials?.password,
            };
          }

          const res = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestBody),
          });

          if (!res.ok) {
            const errorData = await res.json().catch(() => ({}));
            console.error("Auth failed:", errorData);
            return null;
          }

          const data = await res.json();
          
          if (!data?.access) {
            console.error("No access token in response");
            return null;
          }

          const decodedAccess = jwtDecode(data.access) as {
            username: string;
            email: string;
            role: string;
            exp: number;
          };

          console.log("✅ Login successful");
          console.log("Initial refresh token (first 10 chars):", data.refresh?.substring(0, 10) + "...");

          return {
            id: data.user_id?.toString(),
            name: decodedAccess.username ?? credentials?.username,
            email: decodedAccess.email ?? credentials?.email,
            role: decodedAccess.role,
            accessToken: data.access,
            refreshToken: data.refresh,
            accessTokenExpires: decodedAccess.exp * 1000,
            rememberMe: rememberMe,
          };
        } catch (error) {
          console.error("Auth error:", error);
          return null;
        }
      },
    }),
  ],

  callbacks: {
    async jwt({ token, user }: any) {
      // Первый вход
      if (user) {
        console.log("🎯 Initial JWT creation for user:", user.name);
        console.log("Initial refresh token stored (first 10 chars):", user.refreshToken?.substring(0, 10) + "...");
        
        return {
          ...token,
          accessToken: user.accessToken,
          refreshToken: user.refreshToken,
          accessTokenExpires: user.accessTokenExpires,
          rememberMe: user.rememberMe,
          user: {
            id: user.id,
            name: user.name,
            email: user.email,
            role: user.role,
          },
        };
      }

      // Проверяем, нужно ли обновить токен
      const timeLeft = token.accessTokenExpires - Date.now();
      
      if (timeLeft < TOKEN_REFRESH_BUFFER && token.refreshToken) {
        console.log(`⏰ Token expires soon (${new Date(token.accessTokenExpires).toISOString()}), refreshing...`);
        return await refreshAccessToken(token);
      }

      return token;
    },

    async session({ session, token }: any) {
      session.user = token.user;
      session.accessToken = token.accessToken;
      session.error = token.error;
      session.expires = new Date(token.accessTokenExpires).toISOString();
      session.rememberMe = token.rememberMe;
      
      if (token.error) {
        console.log("Session has error:", token.error);
      }
      
      return session;
    },
  },

  session: {
    strategy: "jwt",
    maxAge: SHORT_SESSION_MAX_AGE,
  },

  pages: {
    signIn: "/login",
  },
});

declare module "next-auth" {
  interface Session {
    user?: {
      id: string;
      name: string;
      email: string;
      role: string;
    };
    accessToken?: string;
    error?: string;
    expires?: string;
    rememberMe?: boolean;
  }
  
  interface User {
    id?: string;
    rememberMe?: boolean;
    accessToken?: string;
    refreshToken?: string;
    accessTokenExpires?: number;
    role?: string;
  }
}
