// Визуальные метаданные категорий. Ключ ("key") — это то, что реально
// хранится в backend (scenario.category), см. API_CONTRACT.md:
// management | hiring | team | colleagues | clients | partners
import {
  BriefcaseBusiness,
  UserRound,
  UsersRound,
  Headphones,
  Handshake,
} from 'lucide-react';

export const categories = [
  {
    key: 'management',
    name: 'Общение с руководством',
    icon: BriefcaseBusiness,
    tone: 'lavender',
    description: 'Повышение, ресурсы и решения вверх по иерархии.',
  },
  {
    key: 'hiring',
    name: 'Собеседования и найм',
    icon: UserRound,
    tone: 'mint',
    description: 'Говорить о ценности, деньгах и роли спокойно.',
  },
  {
    key: 'team',
    name: 'Управление командой',
    icon: UsersRound,
    tone: 'peach',
    description: 'Сложные разговоры, дедлайны и обратная связь.',
  },
  {
    key: 'colleagues',
    name: 'Взаимодействие с коллегами',
    icon: UsersRound,
    tone: 'blue',
    description: 'Согласовать ожидания и защитить фокус.',
  },
  {
    key: 'clients',
    name: 'Обслуживание клиентов',
    icon: Headphones,
    tone: 'pink',
    description: 'Сохранить доверие, когда что-то пошло не так.',
  },
  {
    key: 'partners',
    name: 'Переговоры с партнёрами',
    icon: Handshake,
    tone: 'gold',
    description: 'Условия, границы и взаимовыгодные сделки.',
  },
];

export const categoryByKey = Object.fromEntries(categories.map((c) => [c.key, c]));

export function categoryLabel(key) {
  return categoryByKey[key]?.name || key || 'Без категории';
}

export const experienceLevels = [
  { value: 'beginner', label: 'Новичок', hint: 'Лёгкий старт' },
  { value: 'practitioner', label: 'Практик', hint: 'Средний темп' },
  { value: 'expert', label: 'Эксперт', hint: 'Сложные вводные' },
];

export const difficultyLabels = {
  beginner: 'Лёгкий',
  practitioner: 'Средний',
  expert: 'Сложный',
};

export const difficultyXp = {
  beginner: 50,
  practitioner: 100,
  expert: 200,
};
