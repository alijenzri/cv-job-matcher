class UserService:
    def get_user(self, user_id: str):
        # DB lookup
        return {"id": user_id, "email": "user@example.com"}

    def create_user(self, email: str):
        # Create user
        return {"id": "new_id", "email": email}
