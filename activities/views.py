import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import Activity, Registration, Comment


# 辅助函数：检查用户是否为教师
def is_teacher(user):
    return user.is_authenticated and user.profile.role == 'teacher'


# 辅助函数：检查用户是否为学生
def is_student(user):
    return user.is_authenticated and user.profile.role == 'student'

@login_required
@require_http_methods(["GET"])
def activity_list(request):#TODO: 获取所有活动列表


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def create_activity(request):#TODO: 教师创建活动

@login_required
def activity_detail(request, activity_id):#TODO: 获取活动详情

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def register_activity(request, activity_id):#TODO: 学生报名活动

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def cancel_registration(request, activity_id):#TODO: 学生取消报名

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def cancel_activity(request, activity_id):#TODO: 教师取消活动

@login_required
def participants(request, activity_id):#TODO: 教师获取活动参与者列表

@login_required
@csrf_exempt
def comments(request, activity_id):#TODO: 活动评论列表与发表

@login_required
def student_schedule(request):#TODO: 学生获取活动日程表