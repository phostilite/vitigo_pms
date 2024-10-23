from rest_framework import serializers
from .models import Query, QueryTag

class QueryTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueryTag
        fields = ['id', 'name']

class QuerySerializer(serializers.ModelSerializer):
    tags = QueryTagSerializer(many=True, read_only=True)

    class Meta:
        model = Query
        fields = '__all__'