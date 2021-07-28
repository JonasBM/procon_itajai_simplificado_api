from django.contrib import admin

from api import models

admin.site.register(models.Profile)
admin.site.register(models.Processo)
admin.site.register(models.Tipo_de_situacao)
admin.site.register(models.Situcacao)

admin.site.register(models.Documento)
admin.site.register(models.ComentarioDocumento)
