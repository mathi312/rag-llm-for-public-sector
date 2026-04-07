from domain.predefined_questions.question import Question
from domain.predefined_questions.exceptions import (
    QuestionFetchError,
    QuestionCreateError,
    QuestionUpdateError,
)


class QuestionRepository:
    """
    The Repository for saving and retrieving questions form pocketbase.
    """
    def __init__(self, client):
        self.client = client

    def get_most_asked_question_from_pb(self, num_of_questions: int = 4) -> list[Question]:
        """
        Gets the top most asked questions from pb, by default the top 4.
        
        Raises:
            QuestionFetchError: If it fails to fetch the most asked questions from pocketbase.
        """
        try:
            most_asked_questions = self.client.collection("questions").get_list(
                page=1,
                per_page=num_of_questions,
                query_params={"sort": "-times_asked"},
            )

            return [
                Question.from_pb_record(item)
                for item in most_asked_questions.items
            ]
        except Exception as e:
            raise QuestionFetchError(
                f"Failed to fetch top {num_of_questions} most asked questions"
            ) from e


    def get_random_questions(self, exclude: list[Question], num_of_questions: int = 6) -> list[Question]:
        """
        Get random questions from pocketbase excluding the provided questions.
        By default 6 questions are returned.

        Raises:
            QuestionFetchError: If it fails to fetch random questions from pocketbase.
        """
        try:
            exclude_ids = [q.id for q in exclude]

            filter_conditions = " && ".join(
                [f'id != "{qid}"' for qid in exclude_ids]
            )

            all_questions = self.client.collection("questions").get_list(
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
        except Exception as e:
            raise QuestionFetchError(
                f"Failed to fetch {num_of_questions} random questions."
            ) from e


    def exists_by_text(self, question_text: str) -> bool:
        """
        Checks if this question is already in the pocketbase collection.

        Raises:
            QuestionFetchError: If the PocketBase request fails unexpectedly.
        """
        try:
            result = self.client.collection("questions").get_first_list_item(
                f'question = "{question_text}"'
            )
            return result is not None
        except Exception as e:
            # PocketBase raises a 404-style error when no record is found
            error_str = str(e).lower()
            if "404" in error_str or "no records" in error_str or "not found" in error_str:
                # no matching question found in pocketbase
                return False

            raise QuestionFetchError(
                f'Failed to check existence of question: "{question_text}".'
            ) from e


    def create_question(self, question_text: str) -> None:
        """
        Saves the question to pocketbase.

        Raises:
            QuestionCreateError: If the creation of the question failes.
        """
        try:
            self.client.collection("questions").create(
                {
                    "question": question_text,
                    "times_asked": 0,
                }
            )
        except Exception as e:
            raise QuestionCreateError(
                f'Failed to create question: "{question_text}".'
            ) from e


    def increment_times_asked(self, question_id: str) -> None:
        """
        increments the times asked field of the question.

        Raises:
            QuestionUpdateError: If update of the times_asked field fails.
        """
        try:
            self.client.collection("questions").update(
                question_id,
                {"times_asked+": 1}
            )
        except Exception as e:
            raise QuestionUpdateError(
                f"Failed to increment times_asked for question ID: {question_id}."
            ) from e
