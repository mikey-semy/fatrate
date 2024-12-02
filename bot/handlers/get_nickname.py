import g4f
import asyncio
from bot.config import settings
from prefix import get_prefix

async def get_aiprefix(user_id: int, chat_id: int, prompt: str = settings.prompt,) -> str:
    try:
        response = await g4f.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50
        )
        
        return response['choices'][0]['message']['content'].strip()
    
    except Exception as e:
        print(f"Ошибка при получении прозвища нейросетью: {e}")
        return l10n.format_value(get_prefix(user_id, chat_id))
