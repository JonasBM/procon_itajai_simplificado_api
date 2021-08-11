from datetime import datetime
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
import os
from django.dispatch import receiver


def get_system_user():
    username_system = "Sistema"
    first_name = "Sistema"
    user_sistema = User.objects.filter(username=username_system).first()
    if user_sistema:
        return user_sistema
    else:
        return User.objects.create(
            username=username_system, first_name=first_name, is_staff=True, is_active=False, is_superuser=True
        )


class Profile(models.Model):

    user = models.OneToOneField(User, related_name="profile", on_delete=models.CASCADE, unique=True)
    matricula = models.CharField(max_length=255, null=True, blank=True, default="")

    def __str__(self):
        return str(self.user.username)


class Processo(models.Model):
    criado_em = models.DateTimeField(default=timezone.now, blank=True)
    identificacao = models.CharField(max_length=255, null=True, blank=True, default="")
    auto_infracao = models.CharField(max_length=255, null=True, blank=True, default="")
    reclamante = models.CharField(max_length=255, null=True, blank=True, default="")
    reclamada = models.CharField(max_length=255, null=True, blank=True, default="")
    cpf_cnpj = models.CharField(max_length=255, null=True, blank=True, default="")
    ficha_de_atendimento = models.CharField(max_length=255, null=True, blank=True, default="")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return str(self.identificacao) + " - " + str(self.criado_em)

    def ultima_situacao(self):
        return self.situacoes.order_by("-data").all().first()


class Tipo_de_situacao(models.Model):
    ordem = models.PositiveSmallIntegerField(unique=False)
    nome = models.CharField(max_length=255, unique=True)
    css_cor = models.CharField(max_length=10, null=True, blank=True, default="")
    descricao = models.CharField(max_length=255, null=True, blank=True, default="")

    class Meta:
        ordering = ["ordem", "nome", "id"]
        verbose_name_plural = "Tipo_de_situacoes"

    def __str__(self):
        return str(self.ordem) + " - " + str(self.nome)


class Situcacao(models.Model):
    processo = models.ForeignKey(Processo, related_name="situacoes", on_delete=models.CASCADE)
    tipo_de_situacao = models.ForeignKey(Tipo_de_situacao, related_name="situacoes", on_delete=models.CASCADE)
    data = models.DateTimeField(default=timezone.now)
    comentario = models.CharField(max_length=255, null=True, blank=True, default="")

    class Meta:
        ordering = ["processo", "-data", "id"]
        verbose_name_plural = "Situcacoes"

    def __str__(self):
        return str(self.processo) + " - " + str(self.tipo_de_situacao) + " - " + str(self.data)


@receiver(models.signals.post_save, sender=Situcacao)
def auto_comment_on_situacao_save(sender, instance, created, update_fields, **kwargs):
    if created:
        _system_user = get_system_user()
        _comentario = "Novo local: " + instance.tipo_de_situacao.nome
        for documento in instance.processo.documentos.all():
            ComentarioDocumento.objects.create(documento=documento, owner=_system_user, comentario=_comentario)


def processo_id_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/documentos/processo_<processo.id>/<processo.nome>.<filename extension>
    _datetime = datetime.now()
    datetime_str = _datetime.strftime("%Y-%m-%d-%H-%M-%S_")
    return "documentos/processo_{0}/{1}".format(
        instance.processo.id, datetime_str + instance.nome + os.path.splitext(filename)[1]
    )


class Documento(models.Model):
    processo = models.ForeignKey(Processo, related_name="documentos", on_delete=models.CASCADE)
    arquivo = models.FileField(upload_to=processo_id_directory_path)
    nome = models.CharField(max_length=255)
    descricao = models.CharField(max_length=255, null=True, blank=True, default="")
    criado_em = models.DateTimeField(auto_now_add=True)
    ultima_alteracao = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["processo", "-ultima_alteracao", "id"]

    def __str__(self):
        return str(self.processo) + " - " + str(self.arquivo)


@receiver(models.signals.post_delete, sender=Documento)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `Documento` object is deleted.
    """
    if instance.arquivo:
        if os.path.isfile(instance.arquivo.path):
            os.remove(instance.arquivo.path)


@receiver(models.signals.pre_save, sender=Documento)
def auto_delete_file_on_change(sender, instance, **kwargs):

    """
    Deletes old file from filesystem
    when corresponding `Documento` object is updated
    with new file.
    """
    if not instance.pk:
        return False

    try:
        old_document = Documento.objects.get(pk=instance.pk)
    except Documento.DoesNotExist:
        return False

    old_file = old_document.arquivo
    new_file = instance.arquivo

    if (not old_document.nome == instance.nome) and (old_file == new_file):
        dirpath = os.path.dirname(old_document.arquivo.path)
        old_file_name = os.path.basename(old_document.arquivo.path)
        new_file_name = old_file_name[0:20] + instance.nome + os.path.splitext(old_file_name)[1]
        os.rename(os.path.join(dirpath, old_file_name), os.path.join(dirpath, new_file_name))
        instance.arquivo.name = "documentos/processo_{0}/{1}".format(instance.processo.id, new_file_name)

    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)


class ComentarioDocumento(models.Model):
    documento = models.ForeignKey(Documento, related_name="comentarios", on_delete=models.CASCADE)
    owner = models.ForeignKey(User, related_name="comentarios", on_delete=models.CASCADE)
    comentario = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["documento", "id"]

    def __str__(self):
        return str(self.id) + " - " + str(self.documento)
