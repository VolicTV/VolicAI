import random

class CompatibilityManager:
    def __init__(self, user_data_manager, ai_manager):
        self.user_data_manager = user_data_manager
        self.ai_manager = ai_manager

    def calculate_compatibility(self, user1_summary, user2_summary):
        common_words = set(user1_summary.lower().split()) & set(user2_summary.lower().split())
        base_score = len(common_words) * 5
        random_factor = random.randint(-10, 10)
        compatibility = base_score + random_factor
        return max(-100, min(100, compatibility))

    async def generate_compatibility_report(self, user1, user2):
        user1_id = await self.user_data_manager.get_user_info_by_name_or_id(user1)
        user2_id = await self.user_data_manager.get_user_info_by_name_or_id(user2)

        if not user1_id or not user2_id:
            return "I couldn't find one of the users. Make sure both usernames are correct!"

        if user1.lower() == user2.lower():
            return await self.generate_self_compatibility_response(user1)

        user1_summary = await self.user_data_manager.get_user_summary(user1_id, user1)
        user2_summary = await self.user_data_manager.get_user_summary(user2_id, user2)

        compatibility_score = self.calculate_compatibility(user1_summary, user2_summary)

        prompt = f"""
        Generate a concise and fun love compatibility assessment for {user1} and {user2} based on these profiles:
        {user1}: {user1_summary}
        {user2}: {user2_summary}
        
        Use this compatibility percentage: {compatibility_score}%

        Include:
        1. The given compatibility percentage
        2. A brief, witty explanation (2-3 sentences max)
        3. Use many emojis
        
        Keep it short, funny, and slightly adult (18+) with a subtle innuendo.
        Respond in a single message, under 400 characters if possible.
        Use the actual usernames in your response.
        Do not use numbered points or any special formatting.
        """

        compatibility_result = await self.ai_manager.generate_response("", prompt)
        return f"💘 {compatibility_result}"

    async def generate_self_compatibility_response(self, username):
        user_id = await self.user_data_manager.get_user_info_by_name_or_id(username)
        if not user_id:
            return f"I couldn't find user {username}. Are you sure that's the correct username?"

        user_summary = await self.user_data_manager.get_user_summary(user_id, username)
        
        prompt = f"""
        Generate a witty and humorous response for {username} who just tried to check their self-compatibility.
        Use their user profile to personalize the response: {user_summary}
        The response should:
        1. Be lighthearted and funny, but also 18+, and slightly insulting
        2. Include references to their chat history or behavior
        3. Suggest they might need to branch out or meet new people, or are self-centered   
        4. Include many appropriate emoji
        5. Be a single, concise message suitable for Twitch chat, but under 400 characters
        6. Include a 18+ sexual innuendo if possible
        """
        
        self_compatibility_response = await self.ai_manager.generate_enhanced_personalized_response(user_summary, prompt)
        return f"@{username}, {self_compatibility_response}"
