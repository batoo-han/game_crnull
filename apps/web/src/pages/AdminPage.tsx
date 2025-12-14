import { useEffect, useState } from "react";
import {
  adminLogin,
  adminLogout,
  adminMe,
  changeAdminPassword,
  getAdminSettings,
  listPromos,
  putAdminSettings,
  type AdminSettings
} from "../api/admin";

const EMPTY_SETTINGS: AdminSettings = {
  telegram_enabled: true,
  telegram_chat_id: "",
  telegram_template_win: "Победа! Промокод выдан: {code}",
  telegram_template_lose: "Проигрыш",
  promo_ttl_hours: 72,
  promo_daily_limit: 500,
  default_difficulty: "medium",
  theme_json: ""
};

export function AdminPage() {
  const [me, setMe] = useState<{ username: string } | null>(null);
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Проверяем, есть ли секрет в URL
  const hasRouteSecret = !!window.location.pathname.match(/^\/admin\/([^/]+)/);

  const [settings, setSettings] = useState<AdminSettings>(EMPTY_SETTINGS);
  const [promos, setPromos] = useState<Array<{ code: string; created_at: string; expires_at: string; status: string }>>(
    []
  );

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newPassword2, setNewPassword2] = useState("");

  async function refresh() {
    setError(null);
    setBusy(true);
    try {
      const who = await adminMe();
      setMe(who);
      const s = await getAdminSettings();
      setSettings(s);
      const p = await listPromos(50);
      setPromos(p.items);
    } catch (e) {
      setMe(null);
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="min-h-screen px-4 py-10">
      <div className="mx-auto max-w-3xl">
        <div className="glass-card rounded-2xl p-6">
          {!hasRouteSecret && (
            <div className="mb-4 rounded-xl border border-yellow-500/30 bg-yellow-50 p-3 text-sm text-yellow-800">
              ⚠️ Админка может требовать секретный ключ в URL. Если возникают ошибки, попробуйте использовать <code className="bg-yellow-100 px-1 rounded">/admin/&lt;секрет&gt;</code>
            </div>
          )}
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <h1 className="text-2xl font-semibold">Скрытая админка</h1>
            {me && (
              <div className="flex items-center gap-3">
                <div className="text-sm text-[color:var(--text-1)]">Вы вошли как {me.username}</div>
                <button
                  className="btn btn-secondary"
                  onClick={async () => {
                    setBusy(true);
                    try {
                      await adminLogout();
                      setMe(null);
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  Выйти
                </button>
              </div>
            )}
          </div>

          {!me && (
            <div className="mt-6 rounded-2xl border border-black/10 bg-white/70 p-4">
              <h2 className="text-lg font-semibold">Вход</h2>
              <p className="mt-1 text-sm text-[color:var(--text-1)]">
                Используйте учётку, заданную для первичной инициализаци.
              </p>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <label className="text-sm">
                  Логин
                  <input
                    className="mt-1 w-full rounded-xl border border-black/10 bg-white/80 px-3 py-2"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    disabled={busy}
                  />
                </label>
                <label className="text-sm">
                  Пароль
                  <input
                    type="password"
                    className="mt-1 w-full rounded-xl border border-black/10 bg-white/80 px-3 py-2"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={busy}
                  />
                </label>
              </div>
              <div className="mt-4">
                <button
                  className="btn btn-primary"
                  disabled={busy}
                  onClick={async () => {
                    setError(null);
                    setBusy(true);
                    try {
                      await adminLogin(username, password);
                      setPassword("");
                      await refresh();
                    } catch (e) {
                      setError((e as Error).message);
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  Войти
                </button>
              </div>
            </div>
          )}

          {me && (
            <div className="mt-6 grid gap-6">
              <section className="rounded-2xl border border-black/10 bg-white/70 p-4">
                <h2 className="text-lg font-semibold">Смена пароля</h2>
                <p className="mt-1 text-sm text-[color:var(--text-1)]">
                  Рекомендуем длину от 12 символов и уникальный пароль. Пароли не сохраняются в браузере.
                </p>

                <div className="mt-4 grid gap-3 sm:grid-cols-3">
                  <label className="text-sm">
                    Текущий пароль
                    <input
                      type="password"
                      className="mt-1 w-full rounded-xl border border-black/10 bg-white/80 px-3 py-2"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      disabled={busy}
                    />
                  </label>
                  <label className="text-sm">
                    Новый пароль
                    <input
                      type="password"
                      className="mt-1 w-full rounded-xl border border-black/10 bg-white/80 px-3 py-2"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      disabled={busy}
                    />
                  </label>
                  <label className="text-sm">
                    Повторите новый
                    <input
                      type="password"
                      className="mt-1 w-full rounded-xl border border-black/10 bg-white/80 px-3 py-2"
                      value={newPassword2}
                      onChange={(e) => setNewPassword2(e.target.value)}
                      disabled={busy}
                    />
                  </label>
                </div>

                <div className="mt-4">
                  <button
                    className="btn btn-primary"
                    disabled={busy}
                    onClick={async () => {
                      setError(null);
                      if (!currentPassword || !newPassword) {
                        setError("Заполните текущий и новый пароль.");
                        return;
                      }
                      if (newPassword !== newPassword2) {
                        setError("Новый пароль и повтор не совпадают.");
                        return;
                      }
                      setBusy(true);
                      try {
                        await changeAdminPassword(currentPassword, newPassword);
                        setCurrentPassword("");
                        setNewPassword("");
                        setNewPassword2("");
                      } catch (e) {
                        setError((e as Error).message);
                      } finally {
                        setBusy(false);
                      }
                    }}
                  >
                    Сменить пароль
                  </button>
                </div>
              </section>

              <section className="rounded-2xl border border-black/10 bg-white/70 p-4">
                <h2 className="text-lg font-semibold">Настройки</h2>
                <p className="mt-1 text-sm text-[color:var(--text-1)]">
                  Изменения применяются для новых игр и новых уведомлений.
                </p>

                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <label className="text-sm">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={settings.telegram_enabled}
                        onChange={(e) => setSettings({ ...settings, telegram_enabled: e.target.checked })}
                      />
                      Telegram включён
                    </div>
                  </label>

                  <label className="text-sm">
                    Chat ID
                    <input
                      className="mt-1 w-full rounded-xl border border-black/10 bg-white/80 px-3 py-2"
                      value={settings.telegram_chat_id}
                      onChange={(e) => setSettings({ ...settings, telegram_chat_id: e.target.value })}
                    />
                  </label>

                  <label className="text-sm sm:col-span-2">
                    Сообщение о победе (используйте {"{code}"})
                    <input
                      className="mt-1 w-full rounded-xl border border-black/10 bg-white/80 px-3 py-2"
                      value={settings.telegram_template_win}
                      onChange={(e) => setSettings({ ...settings, telegram_template_win: e.target.value })}
                    />
                  </label>

                  <label className="text-sm sm:col-span-2">
                    Сообщение о проигрыше
                    <input
                      className="mt-1 w-full rounded-xl border border-black/10 bg-white/80 px-3 py-2"
                      value={settings.telegram_template_lose}
                      onChange={(e) => setSettings({ ...settings, telegram_template_lose: e.target.value })}
                    />
                  </label>

                  <label className="text-sm">
                    TTL промокода (часы)
                    <input
                      type="number"
                      className="mt-1 w-full rounded-xl border border-black/10 bg-white/80 px-3 py-2"
                      value={settings.promo_ttl_hours}
                      onChange={(e) => setSettings({ ...settings, promo_ttl_hours: Number(e.target.value) })}
                    />
                  </label>

                  <label className="text-sm">
                    Лимит выдач/сутки (0 = без лимита)
                    <input
                      type="number"
                      className="mt-1 w-full rounded-xl border border-black/10 bg-white/80 px-3 py-2"
                      value={settings.promo_daily_limit}
                      onChange={(e) => setSettings({ ...settings, promo_daily_limit: Number(e.target.value) })}
                    />
                  </label>

                  <label className="text-sm">
                    Сложность по умолчанию
                    <select
                      className="mt-1 w-full rounded-xl border border-black/10 bg-white/80 px-3 py-2"
                      value={settings.default_difficulty}
                      onChange={(e) =>
                        setSettings({ ...settings, default_difficulty: e.target.value as AdminSettings["default_difficulty"] })
                      }
                    >
                      <option value="easy">Лёгкая</option>
                      <option value="medium">Уверенная</option>
                      <option value="hard">Сложная</option>
                    </select>
                  </label>

                  <label className="text-sm sm:col-span-2">
                    Тема (JSON, опционально)
                    <textarea
                      className="mt-1 w-full rounded-xl border border-black/10 bg-white/80 px-3 py-2"
                      rows={4}
                      value={settings.theme_json}
                      onChange={(e) => setSettings({ ...settings, theme_json: e.target.value })}
                    />
                  </label>
                </div>

                <div className="mt-4 flex gap-3">
                  <button
                    className="btn btn-primary"
                    disabled={busy}
                    onClick={async () => {
                      setError(null);
                      setBusy(true);
                      try {
                        await putAdminSettings(settings);
                        await refresh();
                      } catch (e) {
                        setError((e as Error).message);
                      } finally {
                        setBusy(false);
                      }
                    }}
                  >
                    Сохранить
                  </button>
                  <button className="btn btn-secondary" disabled={busy} onClick={() => void refresh()}>
                    Обновить
                  </button>
                </div>
              </section>

              <section className="rounded-2xl border border-black/10 bg-white/70 p-4">
                <h2 className="text-lg font-semibold">Последние промокоды</h2>
                <p className="mt-1 text-sm text-[color:var(--text-1)]">Это список выданных кодов (для контроля).</p>
                <div className="mt-4 overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="text-xs text-[color:var(--text-1)]">
                      <tr>
                        <th className="py-2">Код</th>
                        <th className="py-2">Создан</th>
                        <th className="py-2">Истекает</th>
                        <th className="py-2">Статус</th>
                      </tr>
                    </thead>
                    <tbody>
                      {promos.map((p) => (
                        <tr key={`${p.code}-${p.created_at}`} className="border-t border-black/5">
                          <td className="py-2 font-semibold tracking-widest">{p.code}</td>
                          <td className="py-2">{new Date(p.created_at).toLocaleString()}</td>
                          <td className="py-2">{new Date(p.expires_at).toLocaleString()}</td>
                          <td className="py-2">{p.status}</td>
                        </tr>
                      ))}
                      {promos.length === 0 && (
                        <tr>
                          <td className="py-3 text-[color:var(--text-1)]" colSpan={4}>
                            Пока нет данных.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </section>
            </div>
          )}

          {error && (
            <div className="mt-4 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-800">
              {error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


