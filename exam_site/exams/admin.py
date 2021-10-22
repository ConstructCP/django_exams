from django.contrib import admin
from django import forms
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError

from .models import ApplicationUser, Question, QuestionVariant, Exam


class UserCreationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    class Meta:
        model = ApplicationUser
        fields = ('username', 'password')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = ApplicationUser
        fields = ('username', 'password', 'is_active', 'is_admin')


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('username', 'is_admin')
    list_filter = ('is_admin',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Permissions', {'fields': ('is_admin',)})
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password'),
        }),
    )
    search_fields = ('username',)
    ordering = ('username',)
    filter_horizontal = ()


class QuestionVariantInline(admin.TabularInline):
    model = QuestionVariant
    extra = 4
    min_num = 2
    max_num = 4


class QuestionAdmin(admin.ModelAdmin):
    list_display = ['exam', 'title', 'text', 'answer_explanation']
    fieldsets = [
        ('Exam', {'fields': ['exam']}),
        ('Question', {'fields': ['title', 'text']}),
        ('Answer comment', {'fields': ['answer_explanation']})
    ]
    inlines = [QuestionVariantInline]
    list_filter = ['exam']
    search_fields = ['exam']


class ExamAdmin(admin.ModelAdmin):
    list_display = ['title']
    search_fields = ['title']


admin.site.register(ApplicationUser, UserAdmin)
admin.site.unregister(Group)
admin.site.register(Exam, ExamAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(QuestionVariant)
