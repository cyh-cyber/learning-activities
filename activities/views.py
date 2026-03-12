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
def activity_list(request):#获取所有活动列表
    activities = Activity.objects.filter(is_active=True)

    # 筛选
    category = request.GET.get('category')
    if category:
        activities = activities.filter(category=category)

    date_from = request.GET.get('date_from')
    if date_from:
        activities = activities.filter(time__date__gte=date_from)

    # 教师查看自己创建的
    if request.GET.get('created_by_me') == 'true':
        if is_teacher(request.user):
            activities = activities.filter(created_by=request.user)
        else:
            return JsonResponse({'error': 'Permission denied'}, status=403)

    # 手动构建数据
    data = []
    for act in activities:
        data.append({
            'id': act.id,
            'title': act.title,
            'description': act.description,
            'time': act.time.isoformat(),
            'place': act.place,
            'category': act.category,
            'teacher_name': act.created_by.username,
            'is_registered': act.registrations.filter(student=request.user).exists() if is_student(
                request.user) else False,
            'is_active': act.is_active,
        })
    return JsonResponse(data, safe=False)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def create_activity(request):# 教师创建活动
    if not is_teacher(request.user):
        return JsonResponse({'error': 'Only teachers can create activities'}, status=403)

    try:
        data = json.loads(request.body)
        activity = Activity.objects.create(
            title=data['title'],
            description=data.get('description', ''),
            time=data['time'],
            place=data['place'],
            category=data['category'],
            created_by=request.user
        )
        return JsonResponse({
            'id': activity.id,
            'title': activity.title,
            'message': 'Activity created successfully'
        }, status=201)
    except KeyError as e:
        return JsonResponse({'error': f'Missing field: {e}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def cancel_activity(request, activity_id):  #教师取消活动
    if not is_teacher(request.user):
        return JsonResponse({'error': 'Only teachers can cancel activities'}, status=403)

    try:
        activity = Activity.objects.get(pk=activity_id, created_by=request.user)
    except Activity.DoesNotExist:
        return JsonResponse({'error': 'Activity not found or you are not the creator'}, status=404)

    activity.is_active = False
    activity.save()
    return JsonResponse({'message': 'Activity cancelled'})

@login_required
@csrf_exempt
@require_http_methods(["GET"])
def participants(request, activity_id):  #教师获取活动参与者列表
    if not is_teacher(request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    try:
        activity = Activity.objects.get(pk=activity_id, created_by=request.user)
    except Activity.DoesNotExist:
        return JsonResponse({'error': 'Activity not found'}, status=404)

    registrations = activity.registrations.select_related('student').all()
    participants_list = [{
        'id': reg.student.id,
        'username': reg.student.username,
        'email': reg.student.email,
        'registered_at': reg.registered_at.isoformat()
    } for reg in registrations]

    return JsonResponse({
        'activity_title': activity.title,
        'participants': participants_list
    })

@login_required
def activity_detail(request, activity_id):#获取活动详情
    try:
        activity = Activity.objects.get(pk=activity_id, is_active=True)
    except Activity.DoesNotExist:
        return JsonResponse({'error': 'Activity not found'}, status=404)

    data = {
        'id': activity.id,
        'title': activity.title,
        'description': activity.description,
        'time': activity.time.isoformat(),
        'place': activity.place,
        'category': activity.category,
        'teacher_name': activity.created_by.username,
        'is_registered': activity.registrations.filter(student=request.user).exists() if is_student(
            request.user) else False,
    }
    return JsonResponse(data)
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def register_activity(request, activity_id):#TODO: 学生报名活动
    pass
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def cancel_registration(request, activity_id):#TODO: 学生取消报名
    pass

@login_required
@csrf_exempt
def comments(request, activity_id):#TODO: 活动评论列表与发表
    pass
@login_required
def student_schedule(request):#TODO: 学生获取活动日程表
    pass