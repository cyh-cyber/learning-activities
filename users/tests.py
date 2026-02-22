from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from users.models import Profile
import json
from django.test import TestCase

class RegistrationTestCase(TestCase):# user register test
    def setUp(self):
        self.url = reverse('register')

    def test_register_success(self):# user register successful test
        data = {
            'username': 'testuser',
            'password': 'testpassword1',
            'email': 'new@example.com',
            'role': 'student'
        }
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        res_data = response.json()
        self.assertEqual(res_data['user']['username'], 'testuser' )
        self.assertEqual(res_data['user']['role'], 'student')
        user = User.objects.get(username='testuser')
        self.assertEqual(user.profile.role, 'student')

    def test_register_missing_fields(self):  # register missing fields test
        data = {'username': 'newuser'}
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_register_existing_username(self):# register existing username test
        User.objects.create_user(username='existing', password='pass')
        data = {'username': 'existing', 'password': 'pass', 'role': 'student'}
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('already exists', response.json()['error'])


class LoginTest(TestCase):#User login test
    def setUp(self):
        self.url = reverse('login')
        self.user = User.objects.create_user(username='testuser', password='secret')
        self.user.profile.role = 'student'
        self.user.profile.save()

    def test_login_success(self):#login successful test
        data = {'username': 'testuser', 'password': 'secret'}
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertEqual(res_data['user']['username'], 'testuser')
        self.assertEqual(res_data['user']['role'], 'student')
        # 验证 session 已创建
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_login_wrong_password(self):#login wrong password test
        data = {'username': 'testuser', 'password': 'wrong'}
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 401)
        self.assertIn('Invalid credentials', response.json()['error'])

    def test_login_nonexistent_user(self):#login nonexistent user test
        data = {'username': 'nobody', 'password': 'pass'}
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 401)

class LogoutTest(TestCase):#User logout test
    def setUp(self):
        self.url = reverse('logout')
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.client.login(username='testuser', password='pass')  # 先登录

    def test_logout(self):#logout test
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Logout successful')
        # test session has been cleared
        self.assertFalse('_auth_user_id' in self.client.session)
# Create your tests here.
