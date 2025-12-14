export type AdminMe = { username: string };

export type AdminSettings = {
  telegram_enabled: boolean;
  telegram_chat_id: string;
  telegram_template_win: string;
  telegram_template_lose: string;
  promo_ttl_hours: number;
  promo_daily_limit: number;
  default_difficulty: "easy" | "medium" | "hard";
  theme_json: string;
};

export type PromoList = { items: Array<{ code: string; created_at: string; expires_at: string; status: string }> };

function normalizeBaseUrl(raw: string | undefined): string {
  const base = (raw ?? "").trim();
  if (!base) return "";
  return base.endsWith("/") ? base.slice(0, -1) : base;
}

const API_BASE = normalizeBaseUrl(import.meta.env.VITE_API_BASE);

async function adminApi<T>(path: string, init?: RequestInit): Promise<T> {
  // “Скрытая админка”: если открыт URL /admin/<секрет>, то добавляем заголовок.
  // Это не заменяет логин/пароль, а служит дополнительным барьером от перебора URL.
  const m = window.location.pathname.match(/^\/admin\/([^/]+)/);
  const routeSecret = m ? decodeURIComponent(m[1]) : "";
  
  // Определяем, есть ли body и нужно ли устанавливать Content-Type
  const hasBody = init?.body !== undefined && init?.body !== null;
  const isPostOrPut = init?.method === "POST" || init?.method === "PUT";
  
  // Отладка (можно убрать после исправления)
  if (path.includes("/login")) {
    console.log("[adminApi] URL pathname:", window.location.pathname);
    console.log("[adminApi] Route secret extracted:", routeSecret);
    console.log("[adminApi] Request body (raw):", init?.body);
    console.log("[adminApi] Request body (type):", typeof init?.body);
    console.log("[adminApi] Request method:", init?.method);
    console.log("[adminApi] hasBody:", hasBody, "isPostOrPut:", isPostOrPut);
  }
  
  // Собираем заголовки в простом объекте
  const headers: Record<string, string> = {};
  
  // Content-Type устанавливаем только если есть body и это POST/PUT
  if (hasBody && isPostOrPut) {
    headers["Content-Type"] = "application/json";
  }
  
  // Добавляем заголовки из init (если есть)
  if (init?.headers) {
    if (init.headers instanceof Headers) {
      init.headers.forEach((value, key) => {
        headers[key] = value;
      });
    } else if (Array.isArray(init.headers)) {
      for (const [key, value] of init.headers) {
        headers[key] = value;
      }
    } else {
      Object.assign(headers, init.headers);
    }
  }
  
  // Секрет маршрута всегда добавляем в конце (перезаписывает, если был в init.headers)
  if (routeSecret) {
    headers["X-Admin-Route-Secret"] = routeSecret;
  }

  // Собираем параметры запроса явно
  const fetchInit: RequestInit = {
    method: init?.method || "GET",
    credentials: "include"
  };
  
  // Заголовки добавляем только если они есть
  if (Object.keys(headers).length > 0) {
    fetchInit.headers = headers;
  }
  
  // Body добавляем только если он есть (убеждаемся, что это строка)
  if (hasBody) {
    // Если body уже строка - используем как есть, иначе преобразуем
    fetchInit.body = typeof init.body === "string" ? init.body : JSON.stringify(init.body);
  }
  
  // Добавляем остальные опциональные параметры из init
  if (init?.signal) fetchInit.signal = init.signal;
  if (init?.cache) fetchInit.cache = init.cache;
  if (init?.redirect) fetchInit.redirect = init.redirect;

  // Отладка для POST/PUT запросов (особенно для /login)
  if (isPostOrPut && path.includes("/login")) {
    console.log("[adminApi] Final body (string):", fetchInit.body);
    console.log("[adminApi] Final headers:", headers);
    console.log("[adminApi] Full fetchInit:", JSON.stringify({
      method: fetchInit.method,
      credentials: fetchInit.credentials,
      headers: headers,
      body: fetchInit.body
    }, null, 2));
  }

  const res = await fetch(`${API_BASE}${path}`, fetchInit);

  if (!res.ok) {
    let errorMessage = `Ошибка ${res.status}`;
    
    try {
      const text = await res.text();
      // Пытаемся распарсить JSON ответ
      try {
        const json = JSON.parse(text);
        if (json.detail) {
          // Если detail - это массив (валидация Pydantic)
          if (Array.isArray(json.detail)) {
            const errors = json.detail.map((e: any) => {
              if (e.loc && e.msg) {
                const field = e.loc[e.loc.length - 1];
                return `${field}: ${e.msg}`;
              }
              return e.msg || JSON.stringify(e);
            }).join(", ");
            errorMessage = errors || "Ошибка валидации данных";
          } else {
            // Если detail - строка
            errorMessage = json.detail;
          }
        } else if (json.message) {
          errorMessage = json.message;
        } else {
          errorMessage = text || errorMessage;
        }
      } catch {
        // Если не JSON, используем текст как есть
        errorMessage = text || errorMessage;
      }
    } catch {
      // Если не удалось прочитать ответ
      errorMessage = `Ошибка ${res.status}: ${res.statusText}`;
    }
    
    // Специальная обработка для 404 (секрет маршрута)
    if (res.status === 404 && path.startsWith("/api/admin")) {
      if (!routeSecret) {
        errorMessage = "Админка требует секретный ключ в URL. Используйте /admin/<секрет>";
      } else {
        errorMessage = "Неверный секретный ключ в URL или админка недоступна";
      }
    }
    
    // Специальная обработка для 401 (не авторизован)
    if (res.status === 401) {
      if (path.includes("/login")) {
        errorMessage = errorMessage || "Неверный логин или пароль";
      } else {
        errorMessage = errorMessage || "Требуется авторизация";
      }
    }
    
    // Специальная обработка для 422 (ошибка валидации)
    if (res.status === 422) {
      if (path.includes("/login")) {
        errorMessage = errorMessage || "Проверьте правильность введённых данных";
      }
    }
    
    throw new Error(errorMessage);
  }

  return (await res.json()) as T;
}

export async function adminLogin(username: string, password: string): Promise<void> {
  await adminApi("/api/admin/login", { 
    method: "POST", 
    body: { username, password }  // Передаём объект, adminApi сам сериализует
  });
}

export async function adminLogout(): Promise<void> {
  await adminApi("/api/admin/logout", { method: "POST" });
}

export async function adminMe(): Promise<AdminMe> {
  return adminApi<AdminMe>("/api/admin/me", { method: "GET" });
}

export async function getAdminSettings(): Promise<AdminSettings> {
  return adminApi<AdminSettings>("/api/admin/settings", { method: "GET" });
}

export async function putAdminSettings(payload: AdminSettings): Promise<void> {
  await adminApi("/api/admin/settings", { method: "PUT", body: payload });
}

export async function listPromos(limit = 50): Promise<PromoList> {
  return adminApi<PromoList>(`/api/admin/promos?limit=${limit}`, { method: "GET" });
}

export async function changeAdminPassword(currentPassword: string, newPassword: string): Promise<void> {
  await adminApi("/api/admin/change-password", {
    method: "POST",
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
  });
}


