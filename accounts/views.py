import time
import PIL
import io
import datetime
import numpy as np
import base64
import cv2
import mediapipe as mp
import matplotlib.pyplot as plt
import random
import google.generativeai as genai
import textwrap
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from accounts import forms, models
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse

genai.configure(api_key='AIzaSyDhHXZrzaq8DCtwxbVBlPBRkKr8y8Dve0g')
model_text = genai.GenerativeModel('gemini-pro')
model_vision = genai.GenerativeModel('gemini-pro-vision')


mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, model_complexity=2, min_detection_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils


def get_graph_colors():
    graph_colors_ = list(plt.cm.get_cmap('tab20').colors)
    graph_colors = []
    for color in graph_colors_:
        r, b, g = color
        graph_colors.append((int(r * 255), int(g * 255), int(b * 255)))
    return graph_colors


def is_logged_in(request):
    return request.user.is_authenticated


def crop_image(image: InMemoryUploadedFile):
    pil_image = PIL.Image.open(image)

    width, height = pil_image.size
    smaller_side = min(width, height)

    left = (width - smaller_side) // 2
    top = (height - smaller_side) // 2
    right = left + smaller_side
    bottom = top + smaller_side

    square_img = pil_image.crop((left, top, right, bottom))

    image_io = io.BytesIO()
    square_img.save(image_io, format='JPEG')

    image_io.seek(0)

    in_memory_uploaded_file = InMemoryUploadedFile(
        image_io, None, image.name, 'image/jpeg', image_io.tell(), None
    )

    return in_memory_uploaded_file


def get_steps(user, date):
    try:
        steps = models.StepCount.objects.get(user=user, date=date).count
    except models.StepCount.DoesNotExist:
        stepcount = models.StepCount(user=user, date=date)
        stepcount.save()
        steps = stepcount.count
    return steps


def get_steps_week(user):
    weekly_data = []
    running_sum = 0
    for i in range(6, -1, -1):
        date = datetime.date.today() - datetime.timedelta(days=i)
        try:
            steps = get_steps(user, date)
            weekly_data.append((date, steps))
            running_sum += steps
        except models.StepCount.DoesNotExist:
            stepcount = models.StepCount(user=user, date=date)
            stepcount.save()
            weekly_data.append((date, 0))

    avg = running_sum // len(weekly_data)
    return weekly_data, running_sum, avg


def get_sleep(user, date):
    try:
        sleep = models.SleepTrack.objects.get(user=user, date=date)
        sleep = round((sleep.end_time - sleep.start_time).total_seconds() / 3600, 2)
    except models.SleepTrack.DoesNotExist:
        sleep = 0
    return sleep


def get_sleep_week(user):
    weekly_data = []
    valid_counts = 0
    running_sum = 0
    for i in range(7, 0, -1):
        date = datetime.date.today() - datetime.timedelta(days=i)
        try:
            sleep = models.SleepTrack.objects.get(user=user, date=date)
            sleep = round((sleep.end_time - sleep.start_time).total_seconds() / 3600, 2)
            weekly_data.append((date.strftime("%B %d, %Y"), sleep))
            running_sum += sleep
            valid_counts += 1
        except models.SleepTrack.DoesNotExist:
            weekly_data.append((date, 0))

    running_sum = round(running_sum, 2)

    if valid_counts > 0:
        avg = round(running_sum / valid_counts, 2)
    else:
        avg = 0
    return weekly_data, running_sum, avg


def get_physical_activity(user, date):
    total_hours = 0
    activities = models.PhysicalActivity.objects.filter(user=user, start_time__date=date)
    for activity in activities:
        total_hours += round((activity.end_time - activity.start_time).total_seconds() / 3600, 2)
    return total_hours


def get_physical_activity_week(user):
    graph_colors = get_graph_colors()
    activities = set()
    for i in range(7, 0, -1):
        date = datetime.date.today() - datetime.timedelta(days=i)
        activities_ = models.PhysicalActivity.objects.filter(user=user, start_time__date=date)
        for activity in activities_:
            activities.add(activity.activity.name)

    physical_activities_week = dict()
    for activity in activities:
        physical_activities_week[activity] = dict()
        color = random.choice(graph_colors)
        graph_colors.remove(color)
        physical_activities_week[activity]['color'] = color
        physical_activities_week[activity]['values'] = [0] * 7

    dates = []
    physical_activities_daily = []
    for i in range(6, -1, -1):
        date = datetime.date.today() - datetime.timedelta(days=i)
        dates.append(date)
        hours = 0
        activities_ = models.PhysicalActivity.objects.filter(user=user, start_time__date=date)
        for activity in activities_:
            activity_name = activity.activity.name
            duration = round((activity.end_time - activity.start_time).total_seconds() / 3600, 2)
            physical_activities_week[activity_name]['values'][6 - i] += duration
            hours += duration
        physical_activities_daily.append(hours)

    return dates, physical_activities_week, physical_activities_daily


def get_nutrition(user, date):
    calories, fats, carbs, proteins, fibres = 0, 0, 0, 0, 0
    nutrition_entries = models.Nutrition.objects.filter(user=user, date=date)

    for nutrition_entry in nutrition_entries:
        calories += nutrition_entry.amount * nutrition_entry.meal.calories / 100
        fats += nutrition_entry.amount * nutrition_entry.meal.fats / 100
        carbs += nutrition_entry.amount * nutrition_entry.meal.carbs / 100
        proteins += nutrition_entry.amount * nutrition_entry.meal.proteins / 100
        fibres += nutrition_entry.amount * nutrition_entry.meal.fibre / 100

    calories = round(calories, 2)
    fats = round(fats, 2)
    carbs = round(carbs, 2)
    proteins = round(proteins, 2)
    fibres = round(fibres, 2)

    return {
        'calories': calories,
        'fats': fats,
        'carbs': carbs,
        'proteins': proteins,
        'fibres': fibres
    }


def get_nutrition_week(user):
    weekly_data = []
    running_sum = {'calories': 0, 'fats': 0, 'carbs': 0, 'proteins': 0, 'fibres': 0}
    for i in range(6, -1, -1):
        date = datetime.date.today() - datetime.timedelta(days=i)
        day_data = get_nutrition(user, date)

        weekly_data.append((date, day_data))

        running_sum['calories'] += day_data['calories']
        running_sum['fats'] += day_data['fats']
        running_sum['carbs'] += day_data['carbs']
        running_sum['proteins'] += day_data['proteins']
        running_sum['fibres'] += day_data['fibres']

    running_sum['calories'] = round(running_sum['calories'], 2)
    running_sum['fats'] = round(running_sum['fats'], 2)
    running_sum['carbs'] = round(running_sum['carbs'], 2)
    running_sum['proteins'] = round(running_sum['proteins'], 2)
    running_sum['fibres'] = round(running_sum['fibres'], 2)

    avg = {
        'calories': round(running_sum['calories'] / 7, 2),
        'fats': round(running_sum['fats'] / 7, 2),
        'carbs': round(running_sum['carbs'] / 7, 2),
        'proteins': round(running_sum['proteins'] / 7, 2),
        'fibres': round(running_sum['fibres'] / 7, 2)
    }

    return weekly_data, running_sum, avg


def index(request):
    if is_logged_in(request):
        return redirect('profile')
    else:
        return redirect('login')


def login_view(request):
    if is_logged_in(request):
        return redirect('dashboard')

    invalid_data = False
    if request.method == 'POST':
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('dashboard')
        invalid_data = True
    else:
        form = forms.LoginForm()
    return render(request, 'registration/login.html', {'form': form, 'invalid_data': invalid_data})


def signup_view(request):
    if is_logged_in(request):
        return redirect('dashboard')

    errors = None
    if request.method == 'POST':
        form = forms.SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            profile = models.Profile(user=User.objects.get(username=username))
            profile.save()
            return redirect('login')
        else:
            errors = form.errors.as_data()
    else:
        form = forms.SignUpForm()

    context = {'form': form}
    if errors:
        for field, error in errors.items():
            error_ = []
            for err in error:
                error_.append(err.messages[0])
            context[field + '_error'] = error_

    return render(request, 'registration/signup.html', context)


def logout_view(request):
    logout(request)
    return redirect('login')


def dashboard_view(request):
    if not is_logged_in(request):
        return redirect('login')

    context = dict()

    context['steps_today'] = get_steps(request.user, datetime.date.today())
    steps_per_day, steps_week, steps_weekly_avg = get_steps_week(request.user)
    context['steps_per_day'] = steps_per_day
    context['steps_week'] = steps_week
    context['steps_difference'] = context['steps_today'] - steps_weekly_avg

    context['sleep_yesterday'] = get_sleep(request.user, datetime.date.today() - datetime.timedelta(days=1))
    sleep_per_day, sleep_week, sleep_weekly_avg = get_sleep_week(request.user)
    context['sleep_per_day'] = sleep_per_day
    context['sleep_week'] = sleep_week
    context['sleep_difference'] = context['sleep_yesterday'] - sleep_weekly_avg

    physical_dates, physical_activity_week, physical_activity_daily = get_physical_activity_week(request.user)
    context['physical_activity_today'] = get_physical_activity(request.user, datetime.date.today())
    context['physical_activity_difference'] = round(
        context['physical_activity_today'] - round(sum(physical_activity_daily) / len(physical_activity_daily), 2),
        2
    )
    context['physical_dates'] = physical_dates
    context['physical_activity_week'] = physical_activity_week

    context['nutrition_today'] = get_nutrition(request.user, datetime.date.today())
    nutrition_per_day, nutrition_total, nutrition_avg = get_nutrition_week(request.user)
    context['nutrition_calories_diff'] = round(context['nutrition_today']['calories'] - nutrition_avg['calories'], 2)
    context['nutrition_per_day'] = nutrition_per_day
    context['nutrition_total'] = nutrition_total
    context['nutrition_avg'] = nutrition_avg

    return render(request, 'account/dashboard.html', context)


def profile_view(request):
    if not is_logged_in(request):
        return redirect('login')

    return render(request, 'account/profile.html')


def profile_edit_view(request):
    if not is_logged_in(request):
        return redirect('login')

    if request.method == 'POST':
        profile = models.Profile.objects.get(user=request.user)
        profile.first_name = request.POST['first_name']
        profile.last_name = request.POST['last_name']
        profile.email = request.POST['email']
        profile.phone_number = request.POST['phone_number']
        profile.address = request.POST['address']
        profile.city = request.POST['city']
        profile.zip_code = request.POST['zip_code']
        profile.country = request.POST['country']
        profile.save()
        return redirect('profile')

    return render(request, 'account/update_profile.html')


def update_bio(request):
    if not is_logged_in(request):
        return redirect('login')

    if request.POST:
        bio = request.POST['bio']
        bio = bio.strip()
        profile = models.Profile.objects.get(user=request.user)
        profile.bio = bio
        profile.save()

    return redirect('profile')


def update_avatar(request):
    if not is_logged_in(request):
        return redirect('login')

    if request.POST:
        profile = models.Profile.objects.get(user=request.user)
        avatar = request.FILES['avatar']
        avatar = crop_image(avatar)
        profile.avatar = avatar
        profile.save()

    return redirect('profile')


def physical_activity_view(request):
    if not is_logged_in(request):
        return redirect('login')

    context = dict()
    context['steps_today'] = get_steps(request.user, datetime.date.today())
    steps_per_day, steps_week, steps_weekly_avg = get_steps_week(request.user)
    context['steps_per_day'] = steps_per_day
    context['steps_week'] = steps_week
    context['steps_difference'] = context['steps_today'] - steps_weekly_avg

    physical_dates, physical_activity_week, physical_activity_daily = get_physical_activity_week(request.user)
    context['physical_dates'] = physical_dates
    context['physical_activity_week'] = physical_activity_week

    context['physical_form'] = forms.PhysicalActivityForm()

    return render(request, 'account/physical_activities.html', context)


def update_steps(request):
    if not is_logged_in(request):
        return redirect('login')

    if request.POST:
        step_update = request.POST['steps']
        step_update = int(step_update)
        steps = models.StepCount.objects.get(user=request.user, date=datetime.date.today())
        steps.count += step_update
        steps.save()

    return redirect('physical')


def add_physical_activity(request):
    if not is_logged_in(request):
        return redirect('login')

    if request.POST:
        physical_activity = models.PhysicalActivityTypes.objects.get(id=request.POST['activity'])
        physical_activity_entry = models.PhysicalActivity(
            user=request.user,
            activity=physical_activity,
            start_time=request.POST['start_time'],
            end_time=request.POST['end_time'],
        )
        physical_activity_entry.save()

    return redirect('physical')


def sleep_view(request):
    if not is_logged_in(request):
        return redirect('login')

    invalid_duration = False
    if request.POST:
        form = forms.SleepTrackForm(request.POST)
        if form.is_valid():
            date = datetime.date.today() - datetime.timedelta(days=1)
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']
            if end_time < start_time:
                invalid_duration = True
            elif (end_time - start_time).total_seconds() > 24 * 60 * 60:
                invalid_duration = True
            else:
                sleep_track = models.SleepTrack(user=request.user, date=date, start_time=start_time, end_time=end_time)
                sleep_track.save()
    else:
        form = forms.SleepTrackForm()

    try:
        sleep_track = models.SleepTrack.objects.get(user=request.user,
                                                    date=datetime.date.today() - datetime.timedelta(days=1))
        sleep_data_exists = True
    except models.SleepTrack.DoesNotExist:
        sleep_data_exists = False

    context = dict()
    context['sleep_yesterday'] = get_sleep(request.user, datetime.date.today() - datetime.timedelta(days=1))
    sleep_per_day, sleep_week, sleep_weekly_avg = get_sleep_week(request.user)
    context['sleep_per_day'] = sleep_per_day
    context['sleep_week'] = sleep_week
    context['sleep_difference'] = round(context['sleep_yesterday'] - sleep_weekly_avg, 2)
    context['form'] = form
    context['form'] = form
    context['sleep_data_exists'] = sleep_data_exists
    context['invalid_duration'] = invalid_duration

    return render(request, 'account/sleep.html', context)


def nutrition_view(request):
    if not is_logged_in(request):
        return redirect('login')

    if request.method == 'POST':
        form = forms.NutritionForm(request.POST)
        if form.is_valid():
            meal = form.cleaned_data['meal']
            amount = form.cleaned_data['amount']
            time_of_day = form.cleaned_data['time_of_day']
            nutrition = models.Nutrition(
                user=request.user,
                meal=meal,
                amount=amount,
                time_of_day=time_of_day,
                date=datetime.date.today()
            )
            nutrition.save()
            form = forms.NutritionForm()
    else:
        form = forms.NutritionForm()

    context = dict()

    context['nutrition_today'] = get_nutrition(request.user, datetime.date.today())
    nutrition_per_day, nutrition_total, nutrition_avg = get_nutrition_week(request.user)
    context['nutrition_per_day'] = nutrition_per_day
    context['nutrition_total'] = nutrition_total
    context['nutrition_avg'] = nutrition_avg
    context['form'] = form

    return render(request, 'account/nutrition.html', context)


def detectPoseFrame(frame):
    results = pose.process(frame)
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            frame,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
        )

    return frame


def yoga_view(request):
    if not is_logged_in(request):
        return redirect('login')

    show = None
    if request.POST:
        image = PIL.Image.open(request.FILES['image'])
        image = np.array(image, dtype=np.uint8)
        annotated_image = detectPoseFrame(image)
        annotated_image = cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB)
        cv2.imwrite('media/yoga/yoga.jpg', annotated_image)
        show = True

    return render(request, 'account/yoga.html', {'show': show})


def to_format(text):
    text = text.replace('*', ' ')
    return textwrap.indent(text, ' ', predicate=lambda _: True)


def healio_view(request):
    if not is_logged_in(request):
        return redirect('login')

    context = dict()

    if request.POST:
        if request.FILES.get('image'):
            image = PIL.Image.open(request.FILES['image'])
            response = model_vision.generate_content([
                                                         "Extract and interpret the medicine names in the given picture.Also add the description of the medication and what it is used to treat. Answer each new medicine in a separate paragraph",
                                                         image])
            response.resolve()
            formatted_response = to_format(response.text)
            context['response'] = formatted_response
            context['rows'] = max(len(formatted_response) // 60, 5)
        else:
            prompt = request.POST['prompt']
            response = model_text.generate_content(
                f"Answer the following question in the context of health and medicine in a paragraph. {prompt}")
            formatted_response = to_format(response.text)
            context['response'] = formatted_response
            context['rows'] = max(len(formatted_response) // 60, 5)

    return render(request, 'account/healio.html', context)
