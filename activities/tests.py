import json
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



class CreateActivityTestCase(TestCase):
    """测试 create_activity 视图函数"""

    def setUp(self):
        """设置测试数据"""
        self.client = Client()
        self.create_activity_url = reverse('create-activity')

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

        # 准备有效的活动数据
        self.valid_data = {
            'title': 'Test Activity',
            'description': 'Test Description',
            'time': (datetime.now() + timedelta(days=1)).isoformat(),
            'place': 'Test Place',
            'category': 'academic'
        }

    def test_create_activity_success(self):
        """测试教师成功创建活动"""
        self.client.login(username='teacher', password='password123')
        response = self.client.post(
            self.create_activity_url,
            data=json.dumps(self.valid_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn('id', data)
        self.assertIn('title', data)
        self.assertEqual(data['title'], 'Test Activity')
        self.assertEqual(data['message'], 'Activity created successfully')

        # 验证活动已保存到数据库
        activity = Activity.objects.get(id=data['id'])
        self.assertEqual(activity.title, 'Test Activity')
        self.assertEqual(activity.created_by, self.teacher)

    def test_create_activity_student_permission_denied(self):
        """测试学生尝试创建活动被拒绝"""
        self.client.login(username='student', password='password123')
        response = self.client.post(
            self.create_activity_url,
            data=json.dumps(self.valid_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Only teachers can create activities')

    def test_create_activity_unauthenticated(self):
        """测试未认证用户无法创建活动"""
        response = self.client.post(
            self.create_activity_url,
            data=json.dumps(self.valid_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 302)  # 重定向到登录页面

    def test_create_activity_missing_title(self):
        """测试缺少 title 字段时返回错误"""
        self.client.login(username='teacher', password='password123')
        invalid_data = self.valid_data.copy()
        del invalid_data['title']

        response = self.client.post(
            self.create_activity_url,
            data=json.dumps(invalid_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Missing field', data['error'])

    def test_create_activity_missing_time(self):
        """测试缺少 time 字段时返回错误"""
        self.client.login(username='teacher', password='password123')
        invalid_data = self.valid_data.copy()
        del invalid_data['time']

        response = self.client.post(
            self.create_activity_url,
            data=json.dumps(invalid_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Missing field', data['error'])

    def test_create_activity_missing_place(self):
        """测试缺少 place 字段时返回错误"""
        self.client.login(username='teacher', password='password123')
        invalid_data = self.valid_data.copy()
        del invalid_data['place']

        response = self.client.post(
            self.create_activity_url,
            data=json.dumps(invalid_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Missing field', data['error'])

    def test_create_activity_missing_category(self):
        """测试缺少 category 字段时返回错误"""
        self.client.login(username='teacher', password='password123')
        invalid_data = self.valid_data.copy()
        del invalid_data['category']

        response = self.client.post(
            self.create_activity_url,
            data=json.dumps(invalid_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Missing field', data['error'])

    def test_create_activity_description_optional(self):
        """测试 description 字段是可选的"""
        self.client.login(username='teacher', password='password123')
        data_without_description = {
            'title': 'Activity Without Description',
            'time': (datetime.now() + timedelta(days=1)).isoformat(),
            'place': 'Some Place',
            'category': 'sports'
        }

        response = self.client.post(
            self.create_activity_url,
            data=json.dumps(data_without_description),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()

        # 验证活动已创建，description 为空字符串
        activity = Activity.objects.get(id=data['id'])
        self.assertEqual(activity.description, '')

    def test_create_activity_invalid_json(self):
        """测试发送无效 JSON 时的处理"""
        self.client.login(username='teacher', password='password123')

        response = self.client.post(
            self.create_activity_url,
            data='invalid json',
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn('error', data)

    def test_create_activity_all_categories(self):
        """测试创建不同类别的活动"""
        self.client.login(username='teacher', password='password123')

        for category in ['academic', 'sports', 'culture']:
            data = self.valid_data.copy()
            data['category'] = category
            data['title'] = f'{category} Activity'

            response = self.client.post(
                self.create_activity_url,
                data=json.dumps(data),
                content_type='application/json'
            )

            self.assertEqual(response.status_code, 201)
            activity = Activity.objects.get(title=f'{category} Activity')
            self.assertEqual(activity.category, category)


class ActivityDetailTestCase(TestCase):
    """测试 activity_detail 视图函数"""

    def setUp(self):
        """设置测试数据"""
        self.client = Client()

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

        # 创建另一个未报名的学生
        self.student2 = User.objects.create_user(
            username='student2',
            password='password123',
            email='student2@example.com'
        )
        self.student2.profile.role = 'student'
        self.student2.profile.save()

        # 创建活动
        self.activity = Activity.objects.create(
            title='Test Activity',
            description='Test Description',
            time=datetime.now() + timedelta(days=1),
            place='Test Place',
            category='academic',
            created_by=self.teacher,
            is_active=True
        )

        # 创建不活跃的活动
        self.activity_inactive = Activity.objects.create(
            title='Inactive Activity',
            description='Inactive Description',
            time=datetime.now() + timedelta(days=2),
            place='Inactive Place',
            category='sports',
            created_by=self.teacher,
            is_active=False
        )

        # 学生报名活动
        Registration.objects.create(student=self.student, activity=self.activity)

    def test_get_activity_detail_success(self):
        """测试成功获取活动详情"""
        self.client.login(username='student', password='password123')
        response = self.client.get(reverse('activity-detail', kwargs={'activity_id': self.activity.id}))

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 验证返回数据字段
        self.assertIn('id', data)
        self.assertIn('title', data)
        self.assertIn('description', data)
        self.assertIn('time', data)
        self.assertIn('place', data)
        self.assertIn('category', data)
        self.assertIn('teacher_name', data)
        self.assertIn('is_registered', data)

        # 验证具体值
        self.assertEqual(data['id'], self.activity.id)
        self.assertEqual(data['title'], 'Test Activity')
        self.assertEqual(data['description'], 'Test Description')
        self.assertEqual(data['place'], 'Test Place')
        self.assertEqual(data['category'], 'academic')
        self.assertEqual(data['teacher_name'], 'teacher')
        self.assertTrue(data['is_registered'])  # 学生已报名

    def test_get_activity_detail_student_not_registered(self):
        """测试学生获取未报名活动的详情，is_registered 应为 False"""
        self.client.login(username='student2', password='password123')
        response = self.client.get(reverse('activity-detail', kwargs={'activity_id': self.activity.id}))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['is_registered'])  # 学生未报名

    def test_get_activity_detail_teacher(self):
        """测试教师获取活动详情，is_registered 应为 False"""
        self.client.login(username='teacher', password='password123')
        response = self.client.get(reverse('activity-detail', kwargs={'activity_id': self.activity.id}))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['is_registered'])  # 教师的 is_registered 始终为 False
        self.assertEqual(data['teacher_name'], 'teacher')

    def test_get_activity_detail_inactive_activity(self):
        """测试获取不活跃活动的详情，应返回 404"""
        self.client.login(username='student', password='password123')
        response = self.client.get(reverse('activity-detail', kwargs={'activity_id': self.activity_inactive.id}))

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Activity not found')

    def test_get_activity_detail_nonexistent_activity(self):
        """测试获取不存在的活动的详情，应返回 404"""
        self.client.login(username='student', password='password123')
        response = self.client.get(reverse('activity-detail', kwargs={'activity_id': 99999}))

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Activity not found')

    def test_get_activity_detail_unauthenticated(self):
        """测试未认证用户无法获取活动详情"""
        response = self.client.get(reverse('activity-detail', kwargs={'activity_id': self.activity.id}))

        self.assertEqual(response.status_code, 302)  # 重定向到登录页面


    def test_get_activity_detail_all_categories(self):
        """测试获取不同类别活动的详情"""
        self.client.login(username='student', password='password123')

        for category in ['academic', 'sports', 'culture']:
            activity = Activity.objects.create(
                title=f'{category} Activity',
                description=f'{category} Description',
                time=datetime.now() + timedelta(days=1),
                place='Test Place',
                category=category,
                created_by=self.teacher,
                is_active=True
            )

            response = self.client.get(reverse('activity-detail', kwargs={'activity_id': activity.id}))
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data['category'], category)



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


class CancelActivityTestCase(TestCase):
    """测试 cancel_activity 视图函数"""

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

        # 创建活动 - teacher1 创建的活动
        self.activity1 = Activity.objects.create(
            title='Activity 1',
            description='Description 1',
            time=datetime.now() + timedelta(days=1),
            place='Place 1',
            category='academic',
            created_by=self.teacher1,
            is_active=True
        )

        # 创建活动 - teacher2 创建的活动
        self.activity2 = Activity.objects.create(
            title='Activity 2',
            description='Description 2',
            time=datetime.now() + timedelta(days=2),
            place='Place 2',
            category='sports',
            created_by=self.teacher2,
            is_active=True
        )

        # 创建不活跃的活动
        self.activity_inactive = Activity.objects.create(
            title='Inactive Activity',
            description='Inactive Description',
            time=datetime.now() + timedelta(days=3),
            place='Place 3',
            category='culture',
            created_by=self.teacher1,
            is_active=False
        )

    def test_cancel_activity_success(self):
        """测试教师成功取消自己创建的活动"""
        self.client.login(username='teacher1', password='password123')
        url = reverse('cancel-activity', kwargs={'activity_id': self.activity1.id})

        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'Activity cancelled')

        # 验证活动已被标记为不活跃
        self.activity1.refresh_from_db()
        self.assertFalse(self.activity1.is_active)

    def test_cancel_activity_student_permission_denied(self):
        """测试学生尝试取消活动时权限被拒绝"""
        self.client.login(username='student1', password='password123')
        url = reverse('cancel-activity', kwargs={'activity_id': self.activity1.id})

        response = self.client.post(url)

        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Only teachers can cancel activities')

    def test_cancel_activity_unauthenticated(self):
        """测试未认证用户无法取消活动"""
        url = reverse('cancel-activity', kwargs={'activity_id': self.activity1.id})

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)  # 重定向到登录页面

    def test_cancel_activity_not_creator(self):
        """测试教师尝试取消其他教师创建的活动时返回错误"""
        self.client.login(username='teacher1', password='password123')
        url = reverse('cancel-activity', kwargs={'activity_id': self.activity2.id})

        response = self.client.post(url)

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Activity not found or you are not the creator')

    def test_cancel_activity_nonexistent_activity(self):
        """测试取消不存在的活动时返回错误"""
        self.client.login(username='teacher1', password='password123')
        url = reverse('cancel-activity', kwargs={'activity_id': 99999})

        response = self.client.post(url)

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Activity not found or you are not the creator')

    def test_cancel_already_inactive_activity(self):
        """测试取消已经不活跃的活动"""
        self.client.login(username='teacher1', password='password123')
        url = reverse('cancel-activity', kwargs={'activity_id': self.activity_inactive.id})

        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'Activity cancelled')

        # 验证活动仍然保持不活跃状态
        self.activity_inactive.refresh_from_db()
        self.assertFalse(self.activity_inactive.is_active)

    def test_cancel_activity_multiple_times(self):
        """测试多次取消同一活动"""
        self.client.login(username='teacher1', password='password123')
        url = reverse('cancel-activity', kwargs={'activity_id': self.activity1.id})

        # 第一次取消
        response1 = self.client.post(url)
        self.assertEqual(response1.status_code, 200)

        # 第二次取消
        response2 = self.client.post(url)
        self.assertEqual(response2.status_code, 200)

        # 验证活动状态
        self.activity1.refresh_from_db()
        self.assertFalse(self.activity1.is_active)

    def test_cancel_activity_get_method_not_allowed(self):
        """测试使用 GET 方法取消活动时被拒绝"""
        self.client.login(username='teacher1', password='password123')
        url = reverse('cancel-activity', kwargs={'activity_id': self.activity1.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 405)  # Method Not Allowed

    def test_cancel_activity_put_method_not_allowed(self):
        """测试使用 PUT 方法取消活动时被拒绝"""
        self.client.login(username='teacher1', password='password123')
        url = reverse('cancel-activity', kwargs={'activity_id': self.activity1.id})

        response = self.client.put(url)

        self.assertEqual(response.status_code, 405)  # Method Not Allowed

    def test_cancel_activity_delete_method_not_allowed(self):
        """测试使用 DELETE 方法取消活动时被拒绝"""
        self.client.login(username='teacher1', password='password123')
        url = reverse('cancel-activity', kwargs={'activity_id': self.activity1.id})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 405)  # Method Not Allowed


    def test_cancel_activity_delete_method_not_allowed(self):
        """测试使用 DELETE 方法取消活动时被拒绝"""
        self.client.login(username='teacher1', password='password123')
        url = reverse('cancel-activity', kwargs={'activity_id': self.activity1.id})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 405)  # Method Not Allowed


class ParticipantsTestCase(TestCase):
    """测试 participants 视图函数"""

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

        # 创建活动 - teacher1 创建的活动
        self.activity1 = Activity.objects.create(
            title='Activity 1',
            description='Description 1',
            time=datetime.now() + timedelta(days=1),
            place='Place 1',
            category='academic',
            created_by=self.teacher1,
            is_active=True
        )

        # 创建活动 - teacher2 创建的活动
        self.activity2 = Activity.objects.create(
            title='Activity 2',
            description='Description 2',
            time=datetime.now() + timedelta(days=2),
            place='Place 2',
            category='sports',
            created_by=self.teacher2,
            is_active=True
        )

        # 学生报名活动
        self.registration1 = Registration.objects.create(
            student=self.student1,
            activity=self.activity1
        )
        self.registration2 = Registration.objects.create(
            student=self.student2,
            activity=self.activity1
        )

        # 学生报名 teacher2 的活动
        Registration.objects.create(
            student=self.student1,
            activity=self.activity2
        )

    def test_get_participants_success(self):
        """测试教师成功获取自己活动的参与者列表"""
        self.client.login(username='teacher1', password='password123')
        url = reverse('participants', kwargs={'activity_id': self.activity1.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn('activity_title', data)
        self.assertIn('participants', data)
        self.assertEqual(data['activity_title'], 'Activity 1')
        self.assertEqual(len(data['participants']), 2)

        # 验证参与者信息
        participant_ids = [p['id'] for p in data['participants']]
        self.assertIn(self.student1.id, participant_ids)
        self.assertIn(self.student2.id, participant_ids)

        # 验证参与者详细信息
        for participant in data['participants']:
            self.assertIn('id', participant)
            self.assertIn('username', participant)
            self.assertIn('email', participant)
            self.assertIn('registered_at', participant)

    def test_get_participants_student_permission_denied(self):
        """测试学生尝试获取参与者列表时权限被拒绝"""
        self.client.login(username='student1', password='password123')
        url = reverse('participants', kwargs={'activity_id': self.activity1.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Permission denied')

    def test_get_participants_unauthenticated(self):
        """测试未认证用户无法获取参与者列表"""
        url = reverse('participants', kwargs={'activity_id': self.activity1.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)  # 重定向到登录页面

    def test_get_participants_not_creator(self):
        """测试教师尝试获取其他教师活动的参与者列表时返回错误"""
        self.client.login(username='teacher1', password='password123')
        url = reverse('participants', kwargs={'activity_id': self.activity2.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Activity not found')

    def test_get_participants_nonexistent_activity(self):
        """测试获取不存在的活动的参与者列表时返回错误"""
        self.client.login(username='teacher1', password='password123')
        url = reverse('participants', kwargs={'activity_id': 99999})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Activity not found')

    def test_get_participants_empty_list(self):
        """测试获取没有参与者的活动列表"""
        activity_no_participants = Activity.objects.create(
            title='No Participants Activity',
            description='No Participants Description',
            time=datetime.now() + timedelta(days=5),
            place='Place 5',
            category='academic',
            created_by=self.teacher1,
            is_active=True
        )

        self.client.login(username='teacher1', password='password123')
        url = reverse('participants', kwargs={'activity_id': activity_no_participants.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['activity_title'], 'No Participants Activity')
        self.assertEqual(len(data['participants']), 0)

    def test_get_participants_post_method_not_allowed(self):
        """测试使用 POST 方法获取参与者列表时被拒绝"""
        self.client.login(username='teacher1', password='password123')
        url = reverse('participants', kwargs={'activity_id': self.activity1.id})

        response = self.client.post(url)

        self.assertEqual(response.status_code, 405)  # Method Not Allowed

    def test_get_participants_put_method_not_allowed(self):
        """测试使用 PUT 方法获取参与者列表时被拒绝"""
        self.client.login(username='teacher1', password='password123')
        url = reverse('participants', kwargs={'activity_id': self.activity1.id})

        response = self.client.put(url)

        self.assertEqual(response.status_code, 405)  # Method Not Allowed

    def test_get_participants_delete_method_not_allowed(self):
        """测试使用 DELETE 方法获取参与者列表时被拒绝"""
        self.client.login(username='teacher1', password='password123')
        url = reverse('participants', kwargs={'activity_id': self.activity1.id})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 405)  # Method Not Allowed

    def test_get_participants_registered_at_format(self):
        """测试参与者注册时间格式正确"""
        self.client.login(username='teacher1', password='password123')
        url = reverse('participants', kwargs={'activity_id': self.activity1.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 验证 registered_at 是 ISO 格式
        for participant in data['participants']:
            registered_at = participant['registered_at']
            # 尝试解析 ISO 格式，如果能解析说明格式正确
            try:
                datetime.fromisoformat(registered_at.replace('Z', '+00:00'))
            except ValueError:
                self.fail(f"registered_at '{registered_at}' is not in ISO format")

