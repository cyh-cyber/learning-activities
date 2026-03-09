from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import datetime, timedelta
from .models import Activity, Registration
from users.models import Profile


class ActivityListTestCase(TestCase):
    """测试 activity_list 视图函数"""

    def setUp(self):
        """设置测试数据"""
        self.client = Client()

        # 创建教师用户
        self.teacher1 = User.objects.create_user(
            username='teacher1',
            password='password123',
            email='teacher1@example.com'
        )
        self.teacher1.profile.role = 'teacher'
        self.teacher1.profile.save()

        # 创建另一个教师用户
        self.teacher2 = User.objects.create_user(
            username='teacher2',
            password='password123',
            email='teacher2@example.com'
        )
        self.teacher2.profile.role = 'teacher'
        self.teacher2.profile.save()

        # 创建学生用户
        self.student1 = User.objects.create_user(
            username='student1',
            password='password123',
            email='student1@example.com'
        )
        self.student1.profile.role = 'student'
        self.student1.profile.save()

        # 创建学生用户 2
        self.student2 = User.objects.create_user(
            username='student2',
            password='password123',
            email='student2@example.com'
        )
        self.student2.profile.role = 'student'
        self.student2.profile.save()

        # 创建活动
        self.activity1 = Activity.objects.create(
            title='Activity 1',
            description='Description 1',
            time=datetime.now() + timedelta(days=1),
            place='Place 1',
            category='academic',
            created_by=self.teacher1,
            is_active=True
        )

        self.activity2 = Activity.objects.create(
            title='Activity 2',
            description='Description 2',
            time=datetime.now() + timedelta(days=2),
            place='Place 2',
            category='sports',
            created_by=self.teacher1,
            is_active=True
        )

        self.activity3 = Activity.objects.create(
            title='Activity 3',
            description='Description 3',
            time=datetime.now() + timedelta(days=3),
            place='Place 3',
            category='culture',
            created_by=self.teacher2,
            is_active=True
        )

        # 创建不活跃的活动
        self.activity_inactive = Activity.objects.create(
            title='Inactive Activity',
            description='Inactive Description',
            time=datetime.now() + timedelta(days=4),
            place='Place Inactive',
            category='academic',
            created_by=self.teacher1,
            is_active=False
        )

        # 学生报名活动
        Registration.objects.create(student=self.student1, activity=self.activity1)
        Registration.objects.create(student=self.student1, activity=self.activity2)

    def test_get_activity_list_success(self):
        """测试成功获取活动列表"""
        self.client.login(username='student1', password='password123')
        response = self.client.get(reverse('activity-list'))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 3)  # 只有 3 个活跃活动

        # 验证返回数据字段
        activity = data[0]
        self.assertIn('id', activity)
        self.assertIn('title', activity)
        self.assertIn('description', activity)
        self.assertIn('time', activity)
        self.assertIn('place', activity)
        self.assertIn('category', activity)
        self.assertIn('teacher_name', activity)
        self.assertIn('is_registered', activity)
        self.assertIn('is_active', activity)

    def test_filter_by_category(self):
        """测试按类别筛选活动"""
        self.client.login(username='student1', password='password123')
        response = self.client.get(reverse('activity-list'), {'category': 'academic'})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['category'], 'academic')
        self.assertEqual(data[0]['title'], 'Activity 1')

    def test_filter_by_date_from(self):
        """测试按日期筛选活动"""
        self.client.login(username='student1', password='password123')
        future_date = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        response = self.client.get(reverse('activity-list'), {'date_from': future_date})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)  # Activity 2 和 Activity 3

    def test_teacher_view_own_activities_success(self):
        """测试教师查看自己创建的活动"""
        self.client.login(username='teacher1', password='password123')
        response = self.client.get(reverse('activity-list'), {'created_by_me': 'true'})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)  # teacher1 创建了 2 个活跃活动

        for activity in data:
            self.assertEqual(activity['teacher_name'], 'teacher1')

    def test_non_teacher_view_own_activities_permission_denied(self):
        """测试非教师用户查看自己创建的活动时权限被拒绝"""
        self.client.login(username='student1', password='password123')
        response = self.client.get(reverse('activity-list'), {'created_by_me': 'true'})

        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Permission denied')

    def test_student_is_registered_field(self):
        """测试学生的 is_registered 字段正确性"""
        self.client.login(username='student1', password='password123')
        response = self.client.get(reverse('activity-list'))

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 找到对应的活动
        activity1 = next(a for a in data if a['id'] == self.activity1.id)
        activity2 = next(a for a in data if a['id'] == self.activity2.id)
        activity3 = next(a for a in data if a['id'] == self.activity3.id)

        self.assertTrue(activity1['is_registered'])  # 已报名
        self.assertTrue(activity2['is_registered'])  # 已报名
        self.assertFalse(activity3['is_registered'])  # 未报名

    def test_teacher_is_registered_field_always_false(self):
        """测试教师的 is_registered 字段始终为 False"""
        self.client.login(username='teacher1', password='password123')
        response = self.client.get(reverse('activity-list'))

        self.assertEqual(response.status_code, 200)
        data = response.json()

        for activity in data:
            self.assertFalse(activity['is_registered'])

    def test_inactive_activities_not_returned(self):
        """测试不活跃的活动不会被返回"""
        self.client.login(username='student1', password='password123')
        response = self.client.get(reverse('activity-list'))

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 验证不活跃活动不在结果中
        for activity in data:
            self.assertNotEqual(activity['title'], 'Inactive Activity')

    def test_unauthenticated_access(self):
        """测试未认证用户无法访问"""
        response = self.client.get(reverse('activity-list'))

        self.assertEqual(response.status_code, 302)  # 重定向到登录页面

    def test_multiple_filters_combined(self):
        """测试组合使用多个筛选条件"""
        self.client.login(username='student1', password='password123')
        future_date = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        response = self.client.get(reverse('activity-list'), {
            'category': 'academic',
            'date_from': future_date
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        # 应该没有活动满足这两个条件
        print(f"DEBUG: Returned activities: {data}")
        self.assertEqual(len(data), 0)


class IsTeacherIsStudentTestCase(TestCase):
    """测试辅助函数 is_teacher 和 is_student"""

    def setUp(self):
        # 创建教师用户
        self.teacher = User.objects.create_user(
            username='teacher',
            password='password123',
            email='teacher@example.com'
        )
        self.teacher.profile.role = 'teacher'
        self.teacher.profile.save()

        # 创建学生用户
        self.student = User.objects.create_user(
            username='student',
            password='password123',
            email='student@example.com'
        )
        self.student.profile.role = 'student'
        self.student.profile.save()

    def test_is_teacher_with_teacher_user(self):
        """测试 is_teacher 函数识别教师用户"""
        from activities.views import is_teacher
        self.assertTrue(is_teacher(self.teacher))

    def test_is_teacher_with_student_user(self):
        """测试 is_teacher 函数识别学生用户"""
        from activities.views import is_teacher
        self.assertFalse(is_teacher(self.student))

    def test_is_student_with_student_user(self):
        """测试 is_student 函数识别学生用户"""
        from activities.views import is_student
        self.assertTrue(is_student(self.student))

    def test_is_student_with_teacher_user(self):
        """测试 is_student 函数识别教师用户"""
        from activities.views import is_student
        self.assertFalse(is_student(self.teacher))

    def test_is_teacher_with_anonymous_user(self):
        """测试 is_teacher 函数处理匿名用户"""
        from activities.views import is_teacher
        from django.contrib.auth.models import AnonymousUser
        self.assertFalse(is_teacher(AnonymousUser()))

    def test_is_student_with_anonymous_user(self):
        """测试 is_student 函数处理匿名用户"""
        from activities.views import is_student
        from django.contrib.auth.models import AnonymousUser
        self.assertFalse(is_student(AnonymousUser()))

