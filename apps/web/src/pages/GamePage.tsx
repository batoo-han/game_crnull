import { useEffect, useMemo, useState } from "react";
import confetti from "canvas-confetti";
import { motion, AnimatePresence } from "framer-motion";
import { makeMove, newGame, getGiftPromo, type BotDifficulty, type GameState } from "../api/client";
import { WinModal } from "../components/WinModal";
import { GiftSidebar } from "../components/GiftSidebar";
import { generateGift, type GiftType } from "../utils/gifts";
import { playSound } from "../utils/sounds";

const DEFAULT_DIFFICULTY: BotDifficulty = "easy";

// Варианты анимаций для заполнения клеток
const cellAnimations = [
  { scale: [0, 1.2, 1], rotate: [0, 180, 360] },
  { scale: [0, 1], rotate: [0, 360] },
  { scale: [0, 1.1, 1], rotate: [0, -180, 0] },
  { scale: [0, 1], rotate: [0, 90, 0] }
];

function prettyStatus(state: GameState | null): string {
  if (!state) return "Загружаем игру…";
  if (state.status === "IN_PROGRESS") return "Ваш ход";
  if (state.status === "WIN") return "Вы победили!";
  if (state.status === "LOSE") return "Сегодня победил компьютер";
  return "Ничья";
}

function fireSoftConfetti() {
  confetti({
    particleCount: 120,
    spread: 70,
    startVelocity: 26,
    gravity: 0.9,
    ticks: 180,
    colors: ["#d7aefb", "#ffb4c6", "#ffd6a5", "#c7f0bd"]
  });
}

export function GamePage() {
  const [difficulty, setDifficulty] = useState<BotDifficulty>(DEFAULT_DIFFICULTY);
  const [state, setState] = useState<GameState | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showWinModal, setShowWinModal] = useState(false);
  const [gift, setGift] = useState<{ position: number; type: GiftType } | null>(null);
  const [openedCells, setOpenedCells] = useState<Set<number>>(new Set());
  const [collectedGifts, setCollectedGifts] = useState<GiftType[]>([]); // Подарки накапливаются между конами
  const [giftCollectedInThisGame, setGiftCollectedInThisGame] = useState(false); // Флаг: найден ли подарок в текущей игре
  const [cellAnimationsMap, setCellAnimationsMap] = useState<Record<number, number>>({});

  const canPlay = useMemo(() => state?.status === "IN_PROGRESS" && !busy, [state, busy]);

  async function startNewGame(nextDifficulty?: BotDifficulty, resetGifts = false) {
    setError(null);
    setBusy(true);
    setShowWinModal(false);
    
    // Обнуляем подарки только если это выигрыш по подаркам (3 подарка)
    if (resetGifts) {
      setCollectedGifts([]);
    }
    
    // Генерируем новый подарок для текущей игры
    setGift(generateGift());
    setOpenedCells(new Set());
    setGiftCollectedInThisGame(false); // Сбрасываем флаг для новой игры
    setCellAnimationsMap({});
    try {
      const d = nextDifficulty ?? difficulty;
      const s = await newGame(d);
      setState(s);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function onCellClick(cell: number) {
    if (!state || !canPlay) return;
    if (state.board[cell] !== ".") return;

    setError(null);
    setBusy(true);
    
    // Случайная анимация для этой клетки
    const animIndex = Math.floor(Math.random() * cellAnimations.length);
    setCellAnimationsMap((prev) => ({ ...prev, [cell]: animIndex }));
    
    // Звук хода
    playSound("move");
    
    try {
      const s = await makeMove(state.session_id, cell);
      setState(s);
      
      // Отмечаем клетку как открытую игроком
      setOpenedCells((prev) => new Set([...prev, cell]));
      
      // Проверяем подарок под клеткой (только если это ход игрока и подарок ещё не собран в этой игре)
      if (gift && gift.position === cell && !giftCollectedInThisGame) {
        const giftType = gift.type;
        const newCollectedGifts = [...collectedGifts, giftType];
        setCollectedGifts(newCollectedGifts);
        setGiftCollectedInThisGame(true); // Отмечаем, что подарок найден в этой игре
        playSound("gift");
        
        // Если собрали 3 подарка - выдаем промокод
        if (newCollectedGifts.length >= 3) {
          playSound("win");
          fireSoftConfetti();
          
          // Запрашиваем промокод для выигрыша по подаркам
          try {
            const promoResponse = await getGiftPromo(s.session_id);
            // Обновляем состояние с промокодом
            setState({
              ...s,
              promo_code: promoResponse.promo_code,
              promo_expires_at: promoResponse.promo_expires_at,
              status: "WIN"
            });
            setShowWinModal(true);
          } catch (e) {
            // Если не удалось получить промокод, показываем модалку без него
            console.error("Failed to get gift promo:", e);
            setShowWinModal(true);
          }
        }
        // Если подарков < 3, игра продолжается (ничего не делаем)
      }
      
      // Обычная победа в игре (не по подаркам)
      if (s.status === "WIN" && s.promo_code && collectedGifts.length < 3) {
        playSound("win");
        fireSoftConfetti();
        setShowWinModal(true);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    void startNewGame(DEFAULT_DIFFICULTY);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Обработка выигрыша по подаркам уже в onCellClick

  return (
    <div className="min-h-screen px-4 py-6 flex flex-col">
      <div className="mx-auto max-w-2xl w-full flex-1 flex flex-col">
        <header className="mb-4 text-center">
          <h1 className="font-handwritten text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-500 via-purple-500 to-pink-500 tracking-tight">
            Крестики-нолики
          </h1>
          <p className="mt-1 text-sm text-gray-600">
            Небольшая пауза для себя — и один раунд на удачу
          </p>
        </header>

        <div className="glass-card relative overflow-hidden rounded-2xl p-4 flex-1 flex flex-col">
          {/* Декоративные блики */}
          <div className="pointer-events-none absolute -left-20 -top-24 h-64 w-64 rounded-full bg-[radial-gradient(circle_at_30%_30%,rgba(255,180,198,0.55),transparent_60%)] blur-2xl" />
          <div className="pointer-events-none absolute -right-24 -bottom-24 h-72 w-72 rounded-full bg-[radial-gradient(circle_at_30%_30%,rgba(215,174,251,0.55),transparent_60%)] blur-2xl" />

          <div className="relative flex flex-col gap-3 flex-1">
            {/* Статус и управление - компактно */}
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <span className="badge badge-soft">{prettyStatus(state)}</span>
                {state?.status === "IN_PROGRESS" && (
                  <span className="badge badge-soft">
                    Вы: <span className="font-semibold text-[#7a4bff]">X</span>
                  </span>
                )}
                <span className="badge badge-soft">
                  Компьютер: <span className="font-semibold text-[#ff4f8b]">O</span>
                </span>
              </div>

              <div className="flex items-center gap-2">
                <label className="text-xs text-gray-600">
                  Сложность
                  <select
                    className="ml-2 rounded-xl border border-black/10 bg-white/80 px-2 py-1.5 text-sm shadow-sm hover:shadow-md transition-shadow"
                    value={difficulty}
                    onChange={(e) => {
                      const d = e.target.value as BotDifficulty;
                      setDifficulty(d);
                      void startNewGame(d);
                    }}
                    disabled={busy}
                  >
                    <option value="easy">Лёгкая</option>
                    <option value="medium">Уверенная</option>
                    <option value="hard">Сложная</option>
                  </select>
                </label>

                <button
                  className="btn btn-new-game"
                  onClick={() => void startNewGame()}
                  disabled={busy}
                >
                  Новая игра
                </button>
              </div>
            </div>

            {/* Игровое поле - центрируем и ограничиваем размер */}
            <div className="flex-1 flex items-center justify-center">
              <div className="w-full max-w-[360px]">
                <div className="grid grid-cols-3 gap-2.5">
                  {(state?.board ?? Array.from({ length: 9 }, () => ".")).map((cell, idx) => {
                    const filled = cell !== ".";
                    const isOpenedByPlayer = openedCells.has(idx);
                    const hasGift = gift && gift.position === idx;
                    // Показываем подарок только если клетка открыта игроком, заполнена и подарок ещё не собран в этой игре
                    const showGift = hasGift && isOpenedByPlayer && filled && !giftCollectedInThisGame;
                    const animIndex = cellAnimationsMap[idx] ?? 0;
                    const anim = cellAnimations[animIndex] || cellAnimations[0];

                    const cellBase =
                      "cell-card aspect-square rounded-2xl border border-black/10 bg-white/80 shadow-[0_14px_30px_rgba(31,27,46,0.07)] relative overflow-hidden";
                    const cursor = canPlay && !filled ? "cursor-pointer" : "cursor-default";

                    return (
                      <motion.button
                        key={idx}
                        initial={filled ? false : { scale: 1 }}
                        animate={filled ? anim : { scale: 1 }}
                        whileHover={canPlay && !filled ? { scale: 1.05 } : undefined}
                        whileTap={canPlay && !filled ? { scale: 0.98 } : undefined}
                        transition={{ type: "spring", stiffness: 300, damping: 20 }}
                        className={[cellBase, cursor, filled ? "opacity-100" : "hover:shadow-[0_16px_34px_rgba(31,27,46,0.10)]"].join(" ")}
                        onClick={() => void onCellClick(idx)}
                        disabled={!canPlay}
                        aria-label={`Клетка ${idx + 1}`}
                      >
                        {/* Подарок под клеткой (показывается только после открытия игроком) */}
                        {showGift && (
                          <motion.div
                            initial={{ opacity: 0, scale: 0.5 }}
                            animate={{ opacity: 0.3, scale: 1 }}
                            transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
                            className="absolute inset-0 flex items-center justify-center text-4xl pointer-events-none z-0"
                          >
                            {gift.type === "flower" && "🌸"}
                            {gift.type === "jewelry" && "💍"}
                            {gift.type === "gift" && "🎁"}
                            {gift.type === "star" && "⭐"}
                            {gift.type === "heart" && "💖"}
                            {gift.type === "sparkles" && "✨"}
                          </motion.div>
                        )}

                        {/* Узор в клетке */}
                        <span
                          className={[
                            "cell-pattern",
                            cell === "X" ? "cell-pattern-x" : cell === "O" ? "cell-pattern-o" : "cell-pattern-empty"
                          ].join(" ")}
                        />

                        {/* Знак X или O */}
                        <span className="cell-mark-wrap">
                          {cell === "X" ? (
                            <span className="mark mark-x">X</span>
                          ) : cell === "O" ? (
                            <span className="mark mark-o">O</span>
                          ) : (
                            <span className="mark mark-empty">·</span>
                          )}
                        </span>
                      </motion.button>
                    );
                  })}
                </div>
              </div>
            </div>

            {error && (
              <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-800">
                {error}
              </div>
            )}

            {state?.status === "LOSE" && (
              <div className="rounded-2xl border border-black/10 bg-white/70 p-4 text-center">
                <h2 className="text-lg font-semibold mb-2">Сыграем ещё?</h2>
                <p className="text-sm text-gray-600 mb-3">
                  Иногда удача просто на паузе. Один новый раунд — и всё может измениться.
                </p>
                <button className="btn btn-primary" onClick={() => void startNewGame()} disabled={busy}>
                  Сыграть ещё раз
                </button>
              </div>
            )}

            {state?.status === "DRAW" && (
              <div className="rounded-2xl border border-black/10 bg-white/70 p-4 text-center">
                <h2 className="text-lg font-semibold mb-2">Ничья</h2>
                <p className="text-sm text-gray-600 mb-3">Красиво сыграно. Повторим?</p>
                <button className="btn btn-primary" onClick={() => void startNewGame()} disabled={busy}>
                  Новая попытка
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Боковая панель с подарками */}
      {collectedGifts.length > 0 && <GiftSidebar gifts={collectedGifts} />}

      {/* Модальное окно выигрыша */}
      <WinModal
        isOpen={showWinModal}
        promoCode={state?.promo_code ?? null}
        promoExpiresAt={state?.promo_expires_at ?? null}
        onClose={() => {
          setShowWinModal(false);
          // Если это выигрыш по подаркам (3 подарка), обнуляем подарки и начинаем новую игру
          const isGiftWin = collectedGifts.length >= 3;
          void startNewGame(undefined, isGiftWin);
        }}
        isGiftWin={collectedGifts.length >= 3}
      />
    </div>
  );
}
