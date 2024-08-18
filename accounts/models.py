from django.db import models
from django.contrib.auth.models import User

PHYSICAL_ACTIVITY_CATEGORIES = [
    ('Cardio', 'Cardio'),
    ('Strength Training', 'Strength Training'),
    ('Flexibility', 'Flexibility'),
    ('Balance', 'Balance'),
    ('Sports', 'Sports'),
    ('Other', 'Other'),
]

NUTRITION_TIME_CATEGORIES = [
    ('Breakfast', 'Breakfast'),
    ('Lunch', 'Lunch'),
    ('Snack', 'Snack'),
    ('Dinner', 'Dinner'),
]


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(default='avatars/default_avatar.png', upload_to='avatars/')
    phone_number = models.CharField(max_length=13, blank=True)
    address = models.TextField(max_length=500, blank=True)
    city = models.TextField(max_length=50, blank=True)
    state = models.TextField(max_length=50, blank=True)
    country = models.TextField(max_length=50, blank=True)
    zip_code = models.TextField(max_length=50, blank=True)

    def __str__(self):
        return str(self.user.first_name) + ' ' + str(self.user.last_name)


class StepCount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    count = models.IntegerField(default=0)

    class Meta:
        unique_together = (('user', 'date'),)


class SleepTrack(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    class Meta:
        unique_together = (('user', 'date'),)


class PhysicalActivityTypes(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField()
    category = models.CharField(max_length=120, choices=PHYSICAL_ACTIVITY_CATEGORIES)

    def __str__(self):
        return self.name


class PhysicalActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity = models.ForeignKey(PhysicalActivityTypes, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()


class NutritionTypes(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField()
    calories = models.FloatField()
    fats = models.FloatField()
    carbs = models.FloatField()
    proteins = models.FloatField()
    fibre = models.FloatField()

    def __str__(self):
        return self.name


class Nutrition(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meal = models.ForeignKey(NutritionTypes, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()
    time_of_day = models.CharField(max_length=120, choices=NUTRITION_TIME_CATEGORIES)
    date = models.DateField()
