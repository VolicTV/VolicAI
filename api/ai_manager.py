from openai import OpenAI
import config

client = OpenAI(api_key=config.OPENAI_API_KEY)

class AIManager:
    @staticmethod
    async def generate_response(user_summary, prompt):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are VolicTV's witty and sarcastic Twitch chatbot assistant. You love gaming, especially Valorant, and often make playful jabs at VolicTV, or anyone who is a moderator in the chat. Keep responses under 400 characters. Here's a summary of the user you're talking to: " + user_summary},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating AI response: {e}")
            return "I'm sorry, I couldn't generate a response at this time."

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
