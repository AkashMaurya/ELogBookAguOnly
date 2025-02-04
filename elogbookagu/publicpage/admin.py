from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin


# LogYear को एडमिन पैनल में दिखाने के लिए
@admin.register(LogYear)
class LogYearAdmin(admin.ModelAdmin):
    # Admin पैनल में कौन से फील्ड दिखेंगे
    list_display = ("year_name",)
    # सर्च के लिए कौन से फील्ड होंगे
    search_fields = ("year_name",)


# LogYearSection को एडमिन पैनल में दिखाने के लिए
@admin.register(LogYearSection)
class LogYearSectionAdmin(admin.ModelAdmin):
    list_display = ("year_section_name", "year_name")
    # फिल्टर ऑप्शन लॉग ईयर के आधार पर
    list_filter = ("year_name",)
    # सर्च ऑप्शन में year_section_name और year_name शामिल
    search_fields = ("year_section_name", "year_name")


# Department को एडमिन पैनल में दिखाने के लिए
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "log_year", "log_year_section")
    list_filter = ("log_year",)
    search_fields = ("name",)


# Group को एडमिन पैनल में दिखाने के लिए
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("group_name", "log_year", "log_year_section")
    list_filter = ("log_year",)
    search_fields = ("group_name",)


# TrainingSite को एडमिन पैनल में दिखाने के लिए
@admin.register(TrainingSite)
class TrainingSiteAdmin(admin.ModelAdmin):
    list_display = ("name", "log_year")
    list_filter = ("log_year",)
    search_fields = ("name",)
