from openai import OpenAI
import config
import logging
import random

logger = logging.getLogger(__name__)
client = OpenAI(api_key=config.OPENAI_API_KEY)

class AIManager:
    def __init__(self, bot, valorant_manager):
        self.bot = bot
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

    async def generate_roast(self, user_data: dict, target: str) -> str:
        # Extract all messages from user_data
        all_messages = user_data.get('all_messages', [])
        all_quotes = user_data.get('all_quotes', [])    
        
        # Join all messages into a single string, limiting to last 1000 characters if too long
        message_history = " ".join(all_messages)
        if len(message_history) > 1000:
            message_history = message_history[-1000:]

        prompt = f"""Generate a savage, witty roast for {target} based on their chat history:

            Chat history: {message_history}
            Quotes: {all_quotes}

            The roast should be:
            1. Funny and clever
            2. Related to the user's chat history or Valorant stats if available
            3. No more than 3 sentences
            4. Adult Friendly
            5. Include 1-2 appropriate emojis
            6. Reference their chat messages or behavior
            7. If possible, incorporate or reference one of their memorable quotes

            Keep it mean but not too personal."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a mean AI assistant skilled in generating playful roasts based on user data, valorant stats, chat history and quotes."},
                    {"role": "user", "content": prompt}
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating roast: {e}")
            return f"Sorry, I couldn't come up with a roast for {target} right now."
    
    async def generate_volictv_roast(self):
        prompt = """Generate a savage, witty roast for VolicTV, a Valorant Twitch streamer. The roast should:
        1. Be clever and unexpected
        2. Reference Valorant or gaming culture
        3. Include playful jabs at his streaming skills or gameplay
        4. Be slightly edgy but not offensive
        5. Include 1-2 appropriate emojis
        6. Be no longer than 300 characters

        Make it memorable, funny, and tailored to a Valorant streamer!
        """
        return await self.generate_enhanced_personalized_response("", prompt, context="Roasting VolicTV, the Valorant streamer")
    
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
    
    async def generate_enhanced_personalized_response(self, user_summary, prompt, context=""):
        # Combine user summary, prompt, and context into a single prompt
        full_prompt = f"""User profile: {user_summary}

        Generate a witty, personalized response to the following prompt:
        {prompt}

        Additional context: {context}

        The response should:
        1. Be clever and unexpected
        2. Include a touch of playful sarcasm or humor
        3. Reference gaming or Twitch culture if relevant
        4. Include at least one appropriate emoji
        5. Be no longer than 400 characters
        6. Directly address or reference information from the user's profile if applicable

        Make it memorable, funny, and tailored to the user!
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are VolicTV's witty and sarcastic Twitch chatbot assistant. You love gaming, especially Valorant, and often make playful jabs at users."},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating enhanced personalized response: {e}")
            return "I'm sorry, I couldn't generate a witty response at this time."

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
    


