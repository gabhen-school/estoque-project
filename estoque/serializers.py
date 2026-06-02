from rest_framework import serializers
from .models import Produto, MovimentacaoEstoque, Categoria

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'


class ProdutoSerializer(serializers.ModelSerializer):
    estoque_baixo = serializers.BooleanField(read_only=True)

    class Meta:
        model = Produto
        fields = '__all__'


class MovimentacaoEstoqueSerializer(serializers.ModelSerializer):
    # Campo calculado dinamicamente ou lido do model (quantidade x preco_unitario)
    custo_total_financeiro = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = MovimentacaoEstoque
        fields = '__all__'

    def validate(self, data):
        # Validação extra de negócio: impede saída se não houver saldo suficiente
        tipo = data.get('tipo')
        quantidade = data.get('quantidade', 0)
        produto = data.get('produto')

        if quantidade <= 0:
            raise serializers.ValidationError({"quantidade": "A quantidade deve ser maior que zero."})

        if tipo == 'SAIDA' and produto.quantidade < quantidade:
            raise serializers.ValidationError({
                "quantidade": f"Saldo insuficiente em estoque. Disponível: {produto.quantidade}, Solicitado: {quantidade}"
            })
        return data

    def create(self, validated_data):
        produto = validated_data['produto']
        tipo = validated_data['tipo']
        quantidade = validated_data['quantidade']
        
        # 🟢 LÓGICA CORRIGIDA: Atualiza o estoque físico primeiro
        if tipo == 'ENTRADA':
            produto.quantidade += quantidade
        elif tipo == 'SAIDA': # <-- CORRIGIDO: Removido o bug do int()
            produto.quantidade -= quantidade
        elif tipo == 'AJUSTE':
            produto.quantidade = quantidade
            
        # Salva a nova quantidade do produto no banco de dados
        produto.save()
        
        # Cria e retorna a movimentação no banco de dados
        return super().create(validated_data)