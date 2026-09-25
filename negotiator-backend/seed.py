# seed.py
import asyncio
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.scenario import Scenario


async def seed():
    async with AsyncSessionLocal() as db:
        # --- User ---
        existing_user = await db.get(User, "user-1")
        if existing_user is None:
            db.add(User(
                id="user-1",
                email="test@example.com",
                name="Test User"
            ))
            print("[OK] User created: user-1")
        else:
            print("[INFO] User user-1 already exists")

        # --- Scenario 1: Tough Buyer ---
        if await db.get(Scenario, "scenario-1") is None:
            db.add(Scenario(
                id="scenario-1",
                name="Tough Buyer",
                description="Hard-nosed procurement manager. Pushes hard, uses silence, expects a firm justification for every dollar.",
                user_role="Seller",
                user_goal="Sell the batch at no less than $1000 per unit",
                opponent_role="Buyer",
                opponent_character="Tough, skeptical, likes to pressure. Short, clipped sentences.",
                opponent_goal="Buy at $900 per unit or lower",
                opponent_interests=["fast delivery", "2-year warranty"],
                opponent_constraints=["cannot sign without director approval"],
                opponent_red_lines=["rudeness", "lying"],
                concession_limits={"price_min": 900, "max_concessions": 3},
                tactics=["anchor_low", "silence", "take_it_or_leave_it"],
                communication_style="Business-like, short sentences",
                initial_message="Hello. We are short on time. What is your price?"
            ))
            print("[OK] Scenario created: scenario-1 (Tough Buyer)")
        else:
            print("[INFO] Scenario scenario-1 already exists")

        # --- Scenario 2: Friendly Partner ---
        if await db.get(Scenario, "scenario-2") is None:
            db.add(Scenario(
                id="scenario-2",
                name="Friendly Partner",
                description="Open, warm negotiator looking for a long-term partnership. Values trust over squeezing every dollar.",
                user_role="Seller",
                user_goal="Close the deal at $1050 per unit with a 2-year warranty",
                opponent_role="Buyer",
                opponent_character="Friendly, open, chatty. Interested in the person, not just the deal. Looks for win-win.",
                opponent_goal="Get a fair price around $1000 with guaranteed fast delivery",
                opponent_interests=["long-term partnership", "reliable supplier", "fast delivery"],
                opponent_constraints=["budget is tight but flexible for a good partner"],
                opponent_red_lines=["dishonesty", "aggressive pressure"],
                concession_limits={"price_min": 950, "max_concessions": 4},
                tactics=["small_talk", "win_win", "future_value"],
                communication_style="Warm, informal, uses small talk",
                initial_message="Hi! Thanks for making time today. How are things on your side?"
            ))
            print("[OK] Scenario created: scenario-2 (Friendly Partner)")
        else:
            print("[INFO] Scenario scenario-2 already exists")

        # --- Scenario 3: Manipulator ---
        if await db.get(Scenario, "scenario-3") is None:
            db.add(Scenario(
                id="scenario-3",
                name="Manipulator",
                description="Slippery negotiator who uses psychological pressure, fake deadlines, and false alternatives.",
                user_role="Seller",
                user_goal="Close the deal at $1100 per unit without being pressured into concessions",
                opponent_role="Buyer",
                opponent_character="Sly, smooth, uses psychological tricks. Pretends to have other options, invents time pressure.",
                opponent_goal="Get the lowest possible price using pressure and false urgency",
                opponent_interests=["undercutting competitors", "quick signature"],
                opponent_constraints=["must show 'savings' to his boss"],
                opponent_red_lines=["being caught lying", "public pushback"],
                concession_limits={"price_min": 880, "max_concessions": 2},
                tactics=["fake_deadline", "good_cop_bad_cop", "false_scarcity"],
                communication_style="Smooth, indirect, full of hints",
                initial_message="I will be honest with you - I have two other offers on the table. One is quite generous. But I like you. So tell me: what can you do to make this work for both of us?"
            ))
            print("[OK] Scenario created: scenario-3 (Manipulator)")
        else:
            print("[INFO] Scenario scenario-3 already exists")

        await db.commit()
        print("")
        print("Done. Scenarios available:")
        print("  scenario-1  Tough Buyer")
        print("  scenario-2  Friendly Partner")
        print("  scenario-3  Manipulator")
        print("")
        print("Endpoints:")
        print("  GET /api/v1/scenarios          -- list")
        print("  GET /api/v1/scenarios/{id}     -- full details")


if __name__ == "__main__":
    asyncio.run(seed())