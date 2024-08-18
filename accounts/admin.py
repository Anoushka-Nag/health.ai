from django.contrib import admin
from accounts import models


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)


class StepCountAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'count')


class SleepTrackAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'start_time', 'end_time')


class PhysicalActivityTypesAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'category')


class PhysicalActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity', 'start_time', 'end_time')


class NutritionTypesAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'calories')


class NutritionAdmin(admin.ModelAdmin):
    list_display = ('user', 'meal', 'amount', 'time_of_day', 'date')


admin.site.register(models.Profile, ProfileAdmin)
admin.site.register(models.StepCount, StepCountAdmin)
admin.site.register(models.SleepTrack, SleepTrackAdmin)
admin.site.register(models.PhysicalActivityTypes, PhysicalActivityTypesAdmin)
admin.site.register(models.PhysicalActivity, PhysicalActivityAdmin)
admin.site.register(models.NutritionTypes, NutritionTypesAdmin)
admin.site.register(models.Nutrition, NutritionAdmin)
