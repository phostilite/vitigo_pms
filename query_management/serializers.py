from rest_framework import serializers
from .models import Query, QueryTag

class ChoiceSerializer(serializers.Serializer):
    value = serializers.CharField()
    display = serializers.CharField()

class QueryTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueryTag
        fields = ['id', 'name']

class QuerySerializer(serializers.ModelSerializer):
    tags = QueryTagSerializer(many=True, read_only=True)

    class Meta:
        model = Query
        fields = '__all__'
        extra_kwargs = {
            'status': {'required': False},
            'priority': {'required': False},
            'tags': {'required': False}
        }