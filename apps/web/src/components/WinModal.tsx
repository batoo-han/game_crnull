import { motion, AnimatePresence } from "framer-motion";
import confetti from "canvas-confetti";
import { useEffect } from "react";

interface WinModalProps {
  isOpen: boolean;
  promoCode: string | null;
  promoExpiresAt: string | null;
  onClose: () => void;
  isGiftWin?: boolean;
}

export function WinModal({ isOpen, promoCode, promoExpiresAt, onClose, isGiftWin = false }: WinModalProps) {
  useEffect(() => {
    if (isOpen) {
      // Яркий фейерверк при открытии
      const duration = 3000;
      const end = Date.now() + duration;

      const interval = setInterval(() => {
        if (Date.now() > end) {
          clearInterval(interval);
          return;
        }

        confetti({
          particleCount: 3,
          angle: 60,
          spread: 55,
          origin: { x: 0 },
          colors: ["#ff4f8b", "#d7aefb", "#ffd6a5", "#c7f0bd", "#fff"]
        });
        confetti({
          particleCount: 3,
          angle: 120,
          spread: 55,
          origin: { x: 1 },
          colors: ["#ff4f8b", "#d7aefb", "#ffd6a5", "#c7f0bd", "#fff"]
        });
      }, 25);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.8, opacity: 0, y: 20 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.8, opacity: 0, y: 20 }}
          transition={{ type: "spring", damping: 20, stiffness: 300 }}
          className="relative w-full max-w-md rounded-3xl bg-gradient-to-br from-pink-50 via-purple-50 to-pink-100 p-8 shadow-2xl"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Декоративные элементы */}
          <div className="absolute -top-4 -right-4 text-6xl">🎉</div>
          <div className="absolute -bottom-4 -left-4 text-5xl">✨</div>
          <div className="absolute top-1/2 -left-8 text-4xl">🎁</div>
          <div className="absolute top-1/4 -right-8 text-4xl">💝</div>

          <div className="relative text-center">
            <motion.h2
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: "spring" }}
              className="font-handwritten text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-500 via-purple-500 to-pink-500 mb-4"
            >
              {isGiftWin ? "🎁 Три подарка собраны!" : "🎊 Вы победили!"}
            </motion.h2>

            <motion.p
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="text-lg text-gray-700 mb-6 font-medium"
            >
              {isGiftWin
                ? "Вы собрали три подарка! Забирайте промокод на скидку! 🎉"
                : "Это было красиво! Забирайте промокод на скидку! 💖"}
            </motion.p>

            {promoCode && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.4 }}
                className="mb-6"
              >
                <p className="text-sm text-gray-600 mb-2">Ваш промокод:</p>
                <div className="relative inline-block">
                  <div className="absolute inset-0 bg-gradient-to-r from-pink-400 via-purple-400 to-pink-400 rounded-2xl blur-lg opacity-50 animate-pulse" />
                  <div className="relative bg-white rounded-2xl px-6 py-4 border-2 border-purple-300 shadow-xl">
                    <span className="text-3xl font-bold tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-pink-500 to-purple-500">
                      {promoCode}
                    </span>
                  </div>
                </div>
                {promoExpiresAt && (
                  <p className="text-xs text-gray-500 mt-2">
                    Действует до: {new Date(promoExpiresAt).toLocaleString()}
                  </p>
                )}
              </motion.div>
            )}

            <motion.button
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={async () => {
                if (promoCode) {
                  await navigator.clipboard.writeText(promoCode);
                }
                onClose();
              }}
              className="btn-copy-promo relative overflow-hidden rounded-2xl bg-gradient-to-r from-pink-500 via-purple-500 to-pink-500 px-8 py-4 text-white font-bold text-lg shadow-lg hover:shadow-xl transition-all duration-300"
            >
              <span className="relative z-10">
                {promoCode ? "Скопировать и закрыть" : "Закрыть"}
              </span>
              <div className="absolute inset-0 bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 opacity-0 hover:opacity-100 transition-opacity duration-300" />
            </motion.button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

