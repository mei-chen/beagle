from django.contrib import admin
from .models import ClausesStatistic


class ClausesStatisticAdmin(admin.ModelAdmin):
    pass

admin.site.register(ClausesStatistic, ClausesStatisticAdmin)
