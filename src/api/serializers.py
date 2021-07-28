from django.contrib.auth.models import User
from django.db import transaction
from django_typomatic import generate_ts, ts_interface
from rest_framework import serializers

from api import models


@ts_interface()
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
        )
        read_only_fields = (
            "id",
            "first_name",
            "last_name",
        )


@ts_interface()
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Profile
        fields = ("matricula",)


@ts_interface()
class UserProfileSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(required=False)

    last_login = serializers.DateTimeField(read_only=True, format="%Y-%m-%dT%H:%M")
    date_joined = serializers.DateTimeField(read_only=True, format="%Y-%m-%dT%H:%M")

    class Meta:
        model = User
        exclude = ("password",)
        read_only_fields = (
            "last_login",
            "date_joined",
            "is_superuser",
            "groups",
            "user_permissions",
        )

    @transaction.atomic
    def create(self, validated_data):
        profile_data = None
        if "profile" in validated_data.keys():
            profile_data = validated_data.pop("profile")
        user = User.objects.create(**validated_data)
        if profile_data:
            models.Profile.objects.create(user=user, **profile_data)
        else:
            models.Profile.objects.create(user=user)
        return user

    @transaction.atomic
    def update(self, instance, validated_data):
        profile_data = None
        if "profile" in validated_data.keys():
            profile_data = validated_data.pop("profile")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        profile = models.Profile.objects.filter(user=instance).first()
        if not profile:
            profile = models.Profile.objects.create(user=instance)
        if profile_data:
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        return instance


@ts_interface()
class ChangePasswordSerializer(serializers.Serializer):
    model = User
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


@ts_interface()
class Tipo_de_situacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tipo_de_situacao
        fields = "__all__"


@ts_interface()
class SituacaoSerializer(serializers.ModelSerializer):
    data = serializers.DateTimeField(format="%Y-%m-%dT%H:%M")

    class Meta:
        model = models.Situcacao
        fields = (
            "id",
            "processo",
            "tipo_de_situacao",
            "data",
            "comentario",
        )


@ts_interface()
class ProcessoSerializer(serializers.ModelSerializer):
    criado_em = serializers.DateTimeField(format="%Y-%m-%d", read_only=True)
    ultima_situacao = SituacaoSerializer(many=False, read_only=True)

    class Meta:
        model = models.Processo
        fields = (
            "id",
            "criado_em",
            "identificacao",
            "auto_infracao",
            "reclamante",
            "reclamada",
            "cpf_cnpj",
            "ficha_de_atendimento",
            "ultima_situacao",
        )
        read_only_fields = (
            "ultima_situacao",
            "criado_em",
        )


@ts_interface()
class ComentarioDocumentoSerializer(serializers.ModelSerializer):
    criado_em = serializers.DateTimeField(format="%Y-%m-%dT%H:%M", read_only=True)

    class Meta:
        model = models.ComentarioDocumento
        fields = (
            "id",
            "documento",
            "owner",
            "comentario",
            "criado_em",
        )
        read_only_fields = ("criado_em",)


@ts_interface()
class DocumentoSerializer(serializers.ModelSerializer):
    comentarios = ComentarioDocumentoSerializer(many=True, read_only=True)
    criado_em = serializers.DateTimeField(format="%Y-%m-%dT%H:%M", read_only=True)
    ultima_alteracao = serializers.DateTimeField(format="%Y-%m-%dT%H:%M", read_only=True)

    class Meta:
        model = models.Documento
        fields = (
            "id",
            "processo",
            "arquivo",
            "nome",
            "descricao",
            "criado_em",
            "ultima_alteracao",
            "comentarios",
        )
        read_only_fields = (
            "criado_em",
            "ultima_alteracao",
            "comentarios",
        )


generate_ts("./interfacesapi.ts")
