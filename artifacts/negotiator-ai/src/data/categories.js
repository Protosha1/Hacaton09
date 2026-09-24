import {
  BriefcaseBusiness,
  UserRound,
  UsersRound,
  Headphones,
  Target,
} from "lucide-react";

export const categories = [
  {
    name: "Общение с руководством",
    icon: BriefcaseBusiness,
    tone: "lavender",
    description: "Повышение, ресурсы и решения вверх по иерархии.",
  },
  {
    name: "Собеседования и найм",
    icon: UserRound,
    tone: "mint",
    description: "Говорить о ценности, деньгах и роли спокойно.",
  },
  {
    name: "Управление командой",
    icon: UsersRound,
    tone: "peach",
    description: "Сложные разговоры, дедлайны и обратная связь.",
  },
  {
    name: "Взаимодействие с коллегами",
    icon: UsersRound,
    tone: "blue",
    description: "Согласовать ожидания и защитить фокус.",
  },
  {
    name: "Обслуживание клиентов",
    icon: Headphones,
    tone: "pink",
    description: "Сохранить доверие, когда что-то пошло не так.",
  },
  {
    name: "Переговоры с партнёрами",
    icon: Target,
    tone: "gold",
    description: "Условия, границы и взаимовыгодные сделки.",
  },
];

export const cases = [
  {
    id: "raise",
    category: "Общение с руководством",
    title: "Обсуждение повышения",
    description:
      "Подготовьте разговор о расширившейся зоне ответственности и следующем уровне.",
    goal: "Зафиксировать критерии роста и сроки пересмотра компенсации.",
    difficulty: "Средний",
  },
  {
    id: "salary",
    category: "Собеседования и найм",
    title: "Зарплатные ожидания на собеседовании",
    description:
      "Назовите ожидания так, чтобы оставить пространство для диалога.",
    goal: "Обосновать вилку ценностью и получить конкретное предложение.",
    difficulty: "Сложный",
  },
  {
    id: "deadline",
    category: "Управление командой",
    title: "Сложный разговор о дедлайнах",
    description:
      "Команда системно сдвигает сроки. Верните разговор к фактам без обвинений.",
    goal: "Согласовать реалистичный план и ответственность каждого.",
    difficulty: "Средний",
  },
  {
    id: "priority",
    category: "Взаимодействие с коллегами",
    title: "Приоритизация задач",
    description:
      "Коллега просит срочно добавить задачу, но ваш спринт уже заполнен.",
    goal: "Согласовать приоритет через последствия и критерии.",
    difficulty: "Лёгкий",
  },
  {
    id: "refund",
    category: "Обслуживание клиентов",
    title: "Компенсация за сбой",
    description:
      "Клиент требует компенсацию после инцидента. Сначала восстановите доверие.",
    goal: "Признать ущерб и договориться о справедливом решении.",
    difficulty: "Сложный",
  },
  {
    id: "contract",
    category: "Переговоры с партнёрами",
    title: "Пересмотр условий контракта",
    description:
      "Изменились вводные по проекту. Обсудите новые сроки без потери партнёрства.",
    goal: "Обновить условия и сохранить экономику сделки.",
    difficulty: "Сложный",
  },
];

export const defaultUser = {
  name: "Алексей",
  email: "alexey@example.com",
  role: "user",
  status: "pending_onboarding",
  xp: 280,
  difficulty: "Средний",
  categories: ["Управление командой"],
  experience: "Практик",
};
