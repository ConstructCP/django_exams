import json
from typing import IO, Dict, List, Union
from django.core.exceptions import ValidationError

from exams.models import Exam, Question, QuestionVariant


class FileParsingError(Exception):
    pass


class ExamCreate:
    def __init__(self):
        self.parsing_errors = []

    def create_exam(self, title: str, file: IO, source: str, uploader: str = 'application',
                    is_user_uploaded: bool = False) -> Union[None, List]:
        """ Read file, parse question data and save"""
        exam = Exam(title=title, source=source, is_user_uploaded=is_user_uploaded, uploader=uploader)
        json_contents = self.get_json_from_file(file)
        questions = []
        question_answers_variants = []

        try:
            for question_json in json_contents:
                question = self.parse_question_data(question_json, exam)
                variants = self.parse_question_variants(question_json, question)
                questions.append(question)
                question_answers_variants.extend(variants)
        except FileParsingError as e:
            raise ValidationError(str(e))

        if not self.parsing_errors:
            exam.save()
            for q in questions:
                q.save()
            for qv in question_answers_variants:
                qv.save()
            return None
        else:
            return self.parsing_errors

    def get_json_from_file(self, file: IO) -> Dict:
        """ Check file format, decode and parse as JSON """
        raw_contents = file.read()
        file_contents = raw_contents.decode('utf-8') if isinstance(raw_contents, bytes) else raw_contents
        json_contents = json.loads(file_contents)
        return json_contents

    def add_error(self, error: Exception) -> None:
        """ Save error in error list """
        self.parsing_errors.append(error)

    def parse_question_data(self, question_json: dict, exam: Exam) -> Question:
        """ Create Question object from json """
        if not question_json['title']:
            self.add_error(FileParsingError('One of questions doesn\'t have title.'))
        if not question_json['text']:
            self.add_error(FileParsingError(f'Question {question_json["title"]} doesn\'t have question text.'))
        question = Question(exam=exam, title=question_json['title'], text=question_json['text'],
                            answer_explanation=question_json['answer_comment'])
        return question

    def parse_question_variants(self, question_json: dict, question: Question) -> List[QuestionVariant]:
        """ Create several QuestionVariant objects from json """
        correct_answers = question_json['answer']
        if not correct_answers:
            self.add_error(FileParsingError(f'No correct answer marked for question {question_json["title"]}'))
        if not len(question_json['variants']):
            self.add_error(FileParsingError(f'No variants in question {question_json["title"]}'))
        answer_variants = []
        for choice_letter, text in question_json['variants'].items():
            is_correct_answer = choice_letter in correct_answers
            question_variant = QuestionVariant(question=question, choice_letter=choice_letter, text=text,
                                               is_correct_answer=is_correct_answer)
            answer_variants.append(question_variant)
        return answer_variants
