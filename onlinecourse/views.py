from django.shortcuts import render
from django.http import HttpResponseRedirect
# Import all required models
from .models import Course, Enrollment, Question, Choice, Submission
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        user = self.request.user
        if user.is_authenticated:
            course.is_enrolled = check_if_enrolled(user, course)
        context['course'] = course
        return context


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))


# Collect the selected choices from the exam form from the request object
def extract_answers(request):
    submitted_answers = []
    for key in request.POST:
        if key.startswith('choice'):
            value = request.POST[key]
            try:
                choice_id = int(value)
                submitted_answers.append(choice_id)
            except (ValueError, TypeError):
                pass
    return submitted_answers


# Create a submit view to create an exam submission record for a course enrollment
def submit(request, course_id):
    if not request.user.is_authenticated:
        return redirect('onlinecourse:login')

    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    # Get the associated enrollment object or create if not enrolled
    enrollment, _ = Enrollment.objects.get_or_create(user=user, course=course)

    # Collect the selected choices from exam form
    submitted_answer_ids = extract_answers(request)

    # Create a submission object referring to the enrollment
    submission = Submission.objects.create(enrollment=enrollment)
    if submitted_answer_ids:
        choices = Choice.objects.filter(id__in=submitted_answer_ids)
        submission.choices.set(choices)

    # Redirect to show_exam_result with the submission id
    return HttpResponseRedirect(reverse('onlinecourse:show_exam_result', args=(course.id, submission.id)))


# Show exam result view to check if learner passed exam and display results
def show_exam_result(request, course_id, submission_id):
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)

    submitted_choices = submission.choices.all()
    submitted_choice_ids = list(submitted_choices.values_list('id', flat=True))

    questions = course.question_set.all()

    total_score = sum(q.grade for q in questions)
    achieved_score = 0

    for question in questions:
        if question.is_get_score(submitted_choice_ids):
            achieved_score += question.grade

    if total_score > 0:
        grade = round((achieved_score / total_score) * 100)
    else:
        grade = 0

    context = {
        'course': course,
        'submission': submission,
        'submitted_choices': submitted_choices,
        'grade': grade,
    }
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)




