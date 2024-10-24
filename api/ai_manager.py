from openai import OpenAI
import config
import logging
import random

logger = logging.getLogger(__name__)
client = OpenAI(api_key=config.OPENAI_API_KEY)

class AIManager:
    def __init__(self, valorant_manager):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.valorant_manager = valorant_manager

    async def generate_response(self, user_summary, prompt):
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are VolicTV's witty and sarcastic Twitch chatbot assistant. You love gaming, especially Valorant, and often make playful jabs at VolicTV, or anyone who is a moderator in the chat. Keep responses under 400 characters. Here's a summary of the user you're talking to:\n{user_summary}"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating AI response: {e}")
            return "I'm sorry, I couldn't generate a response at this time."

    async def generate_roast(self, user_summary: str, target: str) -> str:

        has_quotes = "No quotes available" not in user_summary
        has_messages = "No recent messages available" not in user_summary

        prompt = f"""Generate a playful roast for {target} based on this user summary:

            {user_summary}

            The roast should be:
            1. Funny and clever, but not overly mean
            2. Related to the user's chat history or quotes if available
            3. No more than 3 sentences
            4. Suitable for Twitch chat (can include mild swearing)
            5. Include 1-2 appropriate emojis
            6. {"Reference their chat messages or behavior" if has_messages else ""}
            7. {"Incorporate or reference one of their quotes" if has_quotes else ""}

            Keep it light-hearted and avoid offensive content."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a witty AI assistant skilled in generating playful roasts based on user data, chat history and quotes."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating roast: {e}")
            return f"Sorry, I couldn't come up with a roast for {target} right now."
    
    async def generate_volictv_roast(self):
        prompt = """
        Generate a witty and playful roast for VolicTV, the streamer and owner of this channel. 
        The roast should be:
        1. Funny and clever, but not overly mean
        2. Related to streaming, gaming (especially Valorant), or being a Twitch personality
        3. Self-deprecating, as if the bot is roasting its own creator
        4. No more than 4 sentences
        5. Suitable for Twitch chat (can swear)
        6. Include many appropriate emojis

        Example: "VolicTV's Valorant skills are so bad, even his own bot could probably beat him. Maybe he should stick to debugging code instead of defusing bombs! 😂"
        """
        return await self.bot.ai_manager.generate_response("", prompt)
    
    async def generate_compliment(self, user_summary, target_user):
        prompt = f"""
        Generate a spicy, witty, and slightly edgy compliment for '{target_user}' based on this user summary: {user_summary}
        The compliment should:
        1. Be clever and unexpected
        2. Include a touch of playful sarcasm or backhanded praise
        3. Reference gaming or Twitch culture if possible
        4. Be slightly flirtatious but not creepy (keep it PG-13)
        5. Include at least one emoji
        6. Be no longer than 300 characters
        Make it memorable and funny!
        """
        return await self.generate_response(user_summary, prompt)
    
    async def enhance_response(self, core_response, context):
        prompt = f"Add a brief, witty comment to this response, but keep the original content intact: '{core_response}'. Context: {context}"
        enhanced_response = await self.generate_response("", prompt)
        if enhanced_response and enhanced_response != core_response:
            return f"{core_response}\n\n {enhanced_response}"
        return core_response

    async def generate_witty_response(self, core_response, context):
        prompt = f"Generate a brief, witty comment about this: '{core_response}'. Context: {context}. Include an appropriate emoji in your response."
        return await self.generate_response("", prompt)

    async def generate_personalized_response(self, user_summary, prompt):
        full_prompt = f"User profile: {user_summary}\n\n{prompt}"
        return await self.generate_response("", full_prompt)
    
    async def generate_rizz(self, user_summary, target_user):
        # Fetch Valorant pick-up lines
        valorant_pickup_lines = await self.valorant_manager.fetch_valorant_pickup_lines()
        
        # Use a few lines as examples in the prompt
        example_lines = "\n".join(random.sample(valorant_pickup_lines, min(15, len(valorant_pickup_lines))))

        prompt = f"""
        Generate a bold and cheeky one-liner for '{target_user}' that includes references to gaming culture and Valorant.
        The one-liner should:
        1. Be daring and playful with a strong innuendo
        2. Include clever wordplay related to Valorant or gaming
        3. Use humor to keep it light-hearted
        4. Include at least one emoji
        5. Be no longer than 150 characters
        Make it spicy, memorable, and a bit naughty!

        Here are some examples of the style and tone:
        {example_lines}
        """
        return await self.generate_response(user_summary, prompt)
    


