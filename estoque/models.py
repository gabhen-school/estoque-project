from django.db import models


class Produto(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.CharField(max_length=250)
    quantidade = models.IntegerField(default=0)
    quantidade_minima = models.IntegerField(default=0)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.nome

    def estoque_baixo(self):
        return self.quantidade <= self.quantidade_minima


class MovimentacaoEstoque(models.Model):
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SAIDA', 'Saída'),
        ('AJUSTE', 'Ajuste'),
    ]

    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    quantidade = models.IntegerField()
    observacao = models.CharField(max_length=250, blank=True)
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo} - {self.produto.nome} ({self.quantidade})"
