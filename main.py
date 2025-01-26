import questionary
import asyncio
from telegram.create_session import create_session
from loguru import logger as ll
from telegram.pin_ai import PinAi
from pathlib import Path



async def choice():
    answers = await questionary.select("Select what you want to do", choices=[
        questionary.Choice("Create Session", 'session'),
        questionary.Choice("Farm PinAI", 'farm'),
        questionary.Choice("Daily Check-in PinAI", 'check in'),
        questionary.Choice("Complite enter tasks (one time tasks)", 'enter_tasks'),
        questionary.Choice("Exit", 'exit')
    ],
    pointer="👉 "
    ).ask_async()
    return answers

async def main():
    task = await choice()
    if task == "session":
        while True:
            await create_session()
            answers = await questionary.select(
                "Do you want to create more sessions?",
                choices=[
                    questionary.Choice("Yes, create one more session", 'yes'),
                    questionary.Choice("No, exit", 'exit'),
                ],
                pointer="👉 "
            ).ask_async()
            if answers == 'exit':
                break

    elif task in ("farm", "check in", "enter_tasks"):
        folder_path = Path("telegram/sessions")
        sessions = [f.name.split('.')[0] for f in folder_path.iterdir() if f.is_file()]
        for session in sessions:
            acc = PinAi(session)
            await acc.start(task)


if __name__ == "__main__":
    asyncio.run(main())







