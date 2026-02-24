import os
import random

from pocketbase import PocketBase

from extensions.question import Question


PB_URL = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8080")
CLIENT = PocketBase(PB_URL)

CLIENT.admins.auth_with_password(
    os.getenv("POCKETBASE_ADMIN_USERNAME"), os.getenv("POCKETBASE_ADMIN_PASSWORD")
)

class QuestionRepository:
    """
    The Repository for saving and retrieving questions form pocketbase.
    """

    def get_most_asked_question_from_pb(self, num_of_questions: int = 4) -> list[Question]:
        """
        Gets the top most asked questions from pb, by default the top 4.
        """
        most_asked_questions = CLIENT.collection("questions").get_list(
            page=1,
            per_page=num_of_questions,
            query_params={"sort": "-times_asked"},
        )

        return [
            Question.from_pb_record(item)
            for item in most_asked_questions.items
        ]


    def get_random_questions(self, exclude: list[Question], num_of_questions: int = 6) -> list[Question]:
        """
        Get random questions from pocketbase excluding the provided questions.
        By default 6 questions are returned.
        """
        exclude_ids = [q.id for q in exclude]

        filter_conditions = " && ".join(
            [f'id != "{qid}"' for qid in exclude_ids]
        )

        all_questions = CLIENT.collection("questions").get_list(
            page=1,
            per_page=num_of_questions,
            query_params={
                "filter": filter_conditions,
                "sort": "@random"
            },
        )

        return [
            Question.from_pb_record(item)
            for item in all_questions.items
        ]


    def exists_by_text(self, question_text: str) -> bool:
        """
        Checks if this question is already in the pocketbase collection.
        """
        try:
            result = CLIENT.collection("questions").get_first_list_item(
                f'question = "{question_text}"'
            )
            return result is not None
        except Exception:
            # No match
            return False


    def create_question(self, question_text: str) -> None:
        """
        Saves the question to pocketbase.
        """
        CLIENT.collection("questions").create(
            {
                "question": question_text,
                "times_asked": 0,
            }
        )

    def increment_times_asked(self, question_id: str) -> None:
        """
        increments the times asked field of the question.
        """
        CLIENT.collection("questions").update(
            question_id,
            {"times_asked+": 1}
        )
