from django.http import Http404
from django.shortcuts import render


exams = ('Exam1', 'Exam2')  # stub variable


def index(request):
    exam_list = exams
    context = {
        'exam_list': exam_list
    }
    return render(request, 'exams/index.html', context)


def exam(request, exam_name):
    if exam_name not in exams:
        raise Http404(f'No exam with name "{exam_name}" found.')
    question_data = questions_stub()
    return render(request, 'exams/exam.html', {'question_data': question_data, 'exam_name': exam_name})


def exam_result(request, exam_name):
    if exam_name not in exams:
        raise Http404(f'No exam with name "{exam_name}" found.')
    question_data = questions_stub()
    correct_answers = 0
    for question in question_data:
        question_text = question['question_text']
        given_answer = request.POST[question_text]
        if int(given_answer) - 1 == question['correct_answer']:
            correct_answers += 1
    score = correct_answers / len(question_data)
    score_percent = int(score * 100)
    return render(request, 'exams/exam_results.html',
                  {'score': score_percent, 'exam_name': exam_name})


def questions_stub():
    questions = ['question1', 'question2', 'question3']
    variants = ['variant1', 'variant2']
    question_data = []
    for question in questions:
        data = {
            'question_text': question,
            'variants': variants,
            'correct_answer': 0
        }
        question_data.append(data)
    return question_data