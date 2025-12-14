// Типы подарков, которые могут быть под клетками
export type GiftType = "flower" | "jewelry" | "gift" | "star" | "heart" | "sparkles";

// Генерируем один подарок под случайной клеткой
export function generateGift(): { position: number; type: GiftType } | null {
  const giftTypes: GiftType[] = ["flower", "jewelry", "gift", "star", "heart", "sparkles"];
  
  // Один подарок под случайной клеткой
  const position = Math.floor(Math.random() * 9);
  const type = giftTypes[Math.floor(Math.random() * giftTypes.length)];
  
  return { position, type };
}

