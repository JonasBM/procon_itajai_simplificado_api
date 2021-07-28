# from django.db.models.aggregates import Count
from api import models, serializers
from api.views.permissions import (
    IsAdminUserOrIsAuthenticatedReadOnly,
    IsAdminUserOrIsOwner,
    IsAdminUserOrIsOwnerOrIsAuthenticatedReadOnly,
)
from django.contrib.auth.models import User
from django.db.models import Case, When
from rest_framework import permissions, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.db.models import Q, Max, F
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.views import exception_handler


class UserProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAdminUserOrIsOwner,
    ]
    serializer_class = serializers.UserProfileSerializer

    def get_queryset(self):
        if self.request.user.is_superuser:
            return User.objects.order_by(
                "first_name",
                "last_name",
            ).all()
        elif self.request.user.is_staff:
            return (
                User.objects.order_by(
                    "first_name",
                    "last_name",
                )
                .filter(is_superuser=False)
                .all()
            )
        else:
            return User.objects.filter(id=self.request.user.id).all()

    def create(self, request, *args, **kwargs):
        if self.request.user.is_staff:
            password = None
            if "password" in request.data.keys():
                password = request.data.pop("password")
            response = super(UserProfileViewSet, self).create(request, *args, **kwargs)
            if password:
                user = User.objects.filter(id=response.data["id"]).first()
                if user:
                    user.set_password(password)
                    user.save()
                    return response
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        if not self.request.user.is_staff:
            request.data.pop("is_superuser")
            request.data.pop("is_staff")
            request.data.pop("is_active")
            request.data.pop("groups")
            request.data.pop("user_permissions")
        else:
            password = None
            if "password" in request.data.keys():
                password = request.data.pop("password")
            if password:
                user = User.objects.filter(id=request.data["id"]).first()
                if user:
                    user.set_password(password)
                    user.save()
        return super(UserProfileViewSet, self).update(request, *args, **kwargs)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated,
    ]
    serializer_class = serializers.UserSerializer

    def get_queryset(self):
        if self.request.user.is_superuser:
            return User.objects.order_by(
                Case(When(id=self.request.user.id, then=0), default=1),
                "first_name",
                "last_name",
            ).all()
        else:
            return User.objects.order_by(
                Case(When(id=self.request.user.id, then=0), default=1),
                "first_name",
                "last_name",
            ).all()


class Tipo_de_situacaoViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAdminUserOrIsAuthenticatedReadOnly,
    ]
    serializer_class = serializers.Tipo_de_situacaoSerializer
    queryset = models.Tipo_de_situacao.objects.all()


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        response.data["num_pages"] = self.page.paginator.num_pages
        return response


class ProcessoViewSet(viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated,
    ]
    serializer_class = serializers.ProcessoSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = models.Processo.objects

        identificacao = self.request.query_params.get("identificacao", None)
        if identificacao:
            queryset = queryset.distinct().filter(identificacao__icontains=identificacao)

        auto_infracao = self.request.query_params.get("auto_infracao", None)
        if auto_infracao:
            queryset = queryset.distinct().filter(auto_infracao__icontains=auto_infracao)

        ficha_de_atendimento = self.request.query_params.get("ficha_de_atendimento", None)
        if ficha_de_atendimento:
            queryset = queryset.distinct().filter(ficha_de_atendimento__icontains=ficha_de_atendimento)

        reclamante = self.request.query_params.get("reclamante", None)
        if reclamante:
            queryset = queryset.distinct().filter(reclamante__unaccent__icontains=reclamante)

        reclamada = self.request.query_params.get("reclamada", None)
        if reclamada:
            queryset = queryset.distinct().filter(reclamada__unaccent__icontains=reclamada)

        cpf_cnpj = self.request.query_params.get("cpf_cnpj", None)
        if cpf_cnpj:
            queryset = queryset.distinct().filter(cpf_cnpj__unaccent__icontains=cpf_cnpj)

        tipo_de_situacao = self.request.query_params.get("tipo_de_situacao", None)
        if tipo_de_situacao:
            queryset = (
                queryset.distinct()
                .annotate(max_date=Max("situacoes__data"))
                .filter(Q(situacoes__data=F("max_date")) & Q(situacoes__tipo_de_situacao=tipo_de_situacao))
            )
        return queryset.order_by("id").all()


class SituacaoViewSet(viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated,
    ]
    serializer_class = serializers.SituacaoSerializer

    def get_queryset(self):
        queryset = models.Situcacao.objects

        processo_id = self.request.query_params.get("processo_id", None)
        if processo_id:
            queryset = queryset.distinct().filter(processo__id=processo_id)
            # queryset = queryset.distinct().filter(processo__id__in=processo_id)

        return queryset.all()


class ComentarioDocumentoViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAdminUserOrIsOwnerOrIsAuthenticatedReadOnly,
    ]
    serializer_class = serializers.ComentarioDocumentoSerializer
    queryset = models.ComentarioDocumento.objects.all()

    def create(self, request, *args, **kwargs):
        request.data["owner"] = request.user.id
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        raise exception_handler.MethodNotAllowed(request.method)


class DocumentoViewSet(viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated,
    ]
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = serializers.DocumentoSerializer

    queryset = models.Documento.objects.all()

    def get_queryset(self):
        queryset = models.Documento.objects
        processo_id = self.request.query_params.get("processo_id", None)
        if processo_id:
            queryset = queryset.distinct().filter(processo__id=processo_id)
        return queryset.all()
