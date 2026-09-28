# seed.py
import asyncio
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.scenario import Scenario


# Все тексты, которые видит пользователь (название, роли, цель, первая реплика),
# и контекст для ИИ-собеседника — на русском.
# Ключи tactics — внутренние теги для промпта, их не переводим.
SCENARIOS = [
    dict(
        id="scenario-1",
        name="Жёсткий закупщик",
        description="Прожжённый менеджер по закупкам. Давит, держит паузы, требует твёрдое обоснование каждого рубля.",
        user_role="Продавец",
        user_goal="Продать партию не дешевле 1000$ за единицу",
        opponent_role="Покупатель",
        opponent_character="Жёсткий, недоверчивый, любит давить. Короткие, рубленые фразы.",
        opponent_goal="Купить по 900$ за единицу или дешевле",
        opponent_interests=["быстрая поставка", "гарантия на 2 года"],
        opponent_constraints=["не может подписать без одобрения директора"],
        opponent_red_lines=["грубость", "ложь"],
        concession_limits={"price_min": 900, "max_concessions": 3},
        tactics=["anchor_low", "silence", "take_it_or_leave_it"],
        communication_style="Деловой, короткие фразы",
        initial_message="Здравствуйте. У нас мало времени. Какая у вас цена?"
    ),
    dict(
        id="scenario-2",
        name="Дружелюбный партнёр",
        description="Открытый, тёплый переговорщик, нацеленный на долгосрочное партнёрство. Ценит доверие больше, чем выжимание каждого рубля.",
        user_role="Продавец",
        user_goal="Закрыть сделку по 1050$ за единицу с гарантией на 2 года",
        opponent_role="Покупатель",
        opponent_character="Дружелюбный, открытый, разговорчивый. Интересуется человеком, а не только сделкой. Ищет вариант, выгодный обеим сторонам.",
        opponent_goal="Получить справедливую цену около 1000$ с гарантированной быстрой поставкой",
        opponent_interests=["долгосрочное партнёрство", "надёжный поставщик", "быстрая поставка"],
        opponent_constraints=["бюджет ограничен, но есть гибкость для хорошего партнёра"],
        opponent_red_lines=["нечестность", "агрессивное давление"],
        concession_limits={"price_min": 950, "max_concessions": 4},
        tactics=["small_talk", "win_win", "future_value"],
        communication_style="Тёплый, неформальный, с элементами светской беседы",
        initial_message="Привет! Спасибо, что нашли время сегодня. Как у вас дела?"
    ),
    dict(
        id="scenario-3",
        name="Манипулятор",
        description="Скользкий переговорщик, который использует психологическое давление, фальшивые дедлайны и мнимые альтернативы.",
        user_role="Продавец",
        user_goal="Закрыть сделку по 1100$ за единицу, не поддавшись давлению на уступки",
        opponent_role="Покупатель",
        opponent_character="Хитрый, обходительный, использует психологические уловки. Делает вид, что есть другие варианты, придумывает нехватку времени.",
        opponent_goal="Получить максимально низкую цену за счёт давления и мнимой срочности",
        opponent_interests=["сбить цену ниже конкурентов", "быстрое подписание"],
        opponent_constraints=["должен показать 'экономию' своему начальнику"],
        opponent_red_lines=["быть пойманным на лжи", "публичное сопротивление"],
        concession_limits={"price_min": 880, "max_concessions": 2},
        tactics=["fake_deadline", "good_cop_bad_cop", "false_scarcity"],
        communication_style="Обходительный, уклончивый, полный намёков",
        initial_message="Буду с вами честен — у меня на столе ещё два предложения. Одно довольно щедрое. Но вы мне нравитесь. Так что скажите: что вы можете сделать, чтобы это сработало для нас обоих?"
    ),
]


async def seed():
    async with AsyncSessionLocal() as db:
        # --- User ---
        existing_user = await db.get(User, "user-1")
        if existing_user is None:
            db.add(User(id="user-1", email="test@example.com", name="Test User"))
            print("[OK] User created: user-1")
        else:
            print("[INFO] User user-1 already exists")

        # --- Scenarios (upsert: существующие строки обновляются, поэтому
        # повторный запуск seed.py переводит уже засеянную БД на русский) ---
        for data in SCENARIOS:
            scenario = await db.get(Scenario, data["id"])
            if scenario is None:
                db.add(Scenario(**data))
                print(f"[OK] Scenario created: {data['id']} ({data['name']})")
            else:
                for key, value in data.items():
                    setattr(scenario, key, value)
                print(f"[OK] Scenario updated: {data['id']} ({data['name']})")

        await db.commit()
        print("")
        print("Done. Scenarios available:")
        for data in SCENARIOS:
            print(f"  {data['id']}  {data['name']}")
        print("")
        print("Endpoints:")
        print("  GET /api/v1/scenarios          -- list")
        print("  GET /api/v1/scenarios/{id}     -- full details")


if __name__ == "__main__":
    asyncio.run(seed())
