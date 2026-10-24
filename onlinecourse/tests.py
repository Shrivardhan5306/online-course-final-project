from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Course, Lesson, Question, Choice, Enrollment, Submission


class AssessmentModelAndScoreTests(TestCase):
    def setUp(self):
        self.course = Course.objects.create(
            name='Cloud Application Development',
            description='Learn how to build cloud apps with Django.'
        )
        self.lesson1 = Lesson.objects.create(
            title='Introduction to Django',
            order=1,
            course=self.course,
            content='Django is a high-level Python web framework.'
        )
        self.question1 = Question.objects.create(
            course=self.course,
            lesson=self.lesson1,
            content='What is Django?',
            grade=50
        )
        self.choice1_correct = Choice.objects.create(
            question=self.question1,
            content='A Python-based web framework',
            is_correct=True
        )
        self.choice1_wrong = Choice.objects.create(
            question=self.question1,
            content='A database system',
            is_correct=False
        )

        self.question2 = Question.objects.create(
            course=self.course,
            lesson=self.lesson1,
            content='Which language is used in Django?',
            grade=50
        )
        self.choice2_correct = Choice.objects.create(
            question=self.question2,
            content='Python',
            is_correct=True
        )
        self.choice2_wrong = Choice.objects.create(
            question=self.question2,
            content='Java',
            is_correct=False
        )

        self.user = User.objects.create_user(
            username='learner1',
            first_name='Shrivardhan',
            last_name='Patil',
            password='testpassword123'
        )
        self.client = Client()

    def test_is_get_score_correct(self):
        # When correct choice is selected
        selected_ids = [self.choice1_correct.id]
        self.assertTrue(self.question1.is_get_score(selected_ids))

    def test_is_get_score_incorrect(self):
        # When incorrect choice is selected
        selected_ids = [self.choice1_wrong.id]
        self.assertFalse(self.question1.is_get_score(selected_ids))

    def test_exam_submission_and_result(self):
        self.client.login(username='learner1', password='testpassword123')

        # Submit exam with correct answers
        post_data = {
            f'choice_{self.choice1_correct.id}': str(self.choice1_correct.id),
            f'choice_{self.choice2_correct.id}': str(self.choice2_correct.id)
        }
        submit_url = reverse('onlinecourse:submit', args=[self.course.id])
        response = self.client.post(submit_url, post_data, follow=True)

        self.assertEqual(response.status_code, 200)
        # Check that result page contains "Congratulations" and score 100
        self.assertContains(response, 'Congratulations')
        self.assertContains(response, '100/100')
        self.assertContains(response, 'Exam results')
