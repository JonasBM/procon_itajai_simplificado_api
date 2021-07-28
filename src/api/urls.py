from django.urls import include, path
from rest_framework import routers

from api.views import generics, viewsets

router = routers.DefaultRouter()
router.register(r"user", viewsets.UserViewSet, "user")
router.register(r"userprofile", viewsets.UserProfileViewSet, "userprofile")
router.register(r"processo", viewsets.ProcessoViewSet, "processo")
router.register(r"tipodesituacao", viewsets.Tipo_de_situacaoViewSet, "tipodesituacao")
router.register(r"situacao", viewsets.SituacaoViewSet, "situacao")
router.register(r"documento", viewsets.DocumentoViewSet, "documento")
router.register(r"comentario", viewsets.ComentarioDocumentoViewSet, "comentario")

urlpatterns = [
    path(r"auth/login/", generics.LoginView.as_view(), name="knox_login"),
    path(r"auth/", include("knox.urls")),
    path(r"changepassword/", generics.ChangePasswordView.as_view()),
    path(r"changetipodesituacaoordem/", generics.ChangeTipoDeSituacaoOrdemView.as_view()),
    path(r"download_documentos_do_processo/", generics.downloadDocumentsFromProcesso.as_view()),
    path(r"download_todos_processos/", generics.downloadTodosProcessos.as_view()),
    path(r"exportar_processos/", generics.exportarProcessos.as_view()),
]

urlpatterns += router.urls
