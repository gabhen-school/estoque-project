from django.db import models
from django.contrib.auth.models import User

class Categoria(models.Model):
    nome = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nome


class Produto(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.CharField(max_length=250, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    quantidade = models.IntegerField(default=0)
    quantidade_minima = models.IntegerField(default=0)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Novas propriedades de Localização e Integração
    localizacao_deposito = models.CharField(max_length=100, blank=True, help_text="Ex: Corredor A, Prateleira 3")
    fornecedor_id = models.IntegerField(null=True, blank=True, help_text="ID do parceiro do Módulo de Fornecedores")
    cliente_reserva_id = models.IntegerField(null=True, blank=True, help_text="ID do Cliente se o item estiver reservado")
    status_reserva = models.BooleanField(default=False)

    def __str__(self):
        return self.nome

    @property
    def estoque_baixo(self):
        return self.quantidade <= self.quantidade_minima


class MovimentacaoEstoque(models.Model):
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SAIDA', 'Saída'),
        ('AJUSTE', 'Ajuste'),
    ]

    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='movimentacoes')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    quantidade = models.IntegerField()
    observacao = models.CharField(max_length=250, blank=True)
    data = models.DateTimeField(auto_now_add=True)
    
    # Integrações internas e externas
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, help_text="Quem realizou")
    custo_total_financeiro = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Qtd x Preço no momento")

    def __str__(self):
        return f"{self.tipo} - {self.produto.nome} ({self.quantidade})"

    def save(self, *args, **kwargs):
        # Calcula automaticamente o impacto financeiro para o outro módulo ler
        if self.produto:
            self.custo_total_financeiro = self.quantidade * self.produto.preco_unitario
        super().save(*args, **kwargs)