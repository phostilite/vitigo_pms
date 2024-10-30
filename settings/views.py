from django.shortcuts import render
from django.views import View

class SettingsManagementView(View):
    def get(self, request):
        return render(request, 'dashboard/admin/settings/settings.html')
