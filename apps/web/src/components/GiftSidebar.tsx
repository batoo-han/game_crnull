import { motion } from "framer-motion";

interface GiftSidebarProps {
  gifts: string[];
}

const giftEmojis: Record<string, string> = {
  flower: "🌸",
  jewelry: "💍",
  gift: "🎁",
  star: "⭐",
  heart: "💖",
  sparkles: "✨"
};

export function GiftSidebar({ gifts }: GiftSidebarProps) {
  if (gifts.length === 0) return null;

  return (
    <motion.div
      initial={{ x: -100, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      className="fixed left-4 top-1/2 -translate-y-1/2 z-40"
    >
      <div className="bg-white/90 backdrop-blur-md rounded-2xl p-4 shadow-xl border border-purple-200">
        <h3 className="text-sm font-semibold text-gray-700 mb-3 text-center">Подарки</h3>
        <div className="flex flex-col gap-2">
          {gifts.map((gift, idx) => (
            <motion.div
              key={idx}
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ delay: idx * 0.1, type: "spring", stiffness: 200 }}
              className="text-3xl text-center p-2 bg-gradient-to-br from-pink-100 to-purple-100 rounded-xl"
            >
              {giftEmojis[gift] || "🎁"}
            </motion.div>
          ))}
        </div>
        {gifts.length > 0 && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="mt-3 text-center text-xs font-bold text-purple-600"
          >
            🎁 Подарок!
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}

