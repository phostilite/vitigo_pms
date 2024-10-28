from rest_framework import serializers
from .models import Query, QueryTag, QueryAttachment

class ChoiceSerializer(serializers.Serializer):
    value = serializers.CharField()
    display = serializers.CharField()

class QueryTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueryTag
        fields = ['id', 'name']

class QueryAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueryAttachment
        fields = ['id', 'file', 'uploaded_at']

class QuerySerializer(serializers.ModelSerializer):
    tags = QueryTagSerializer(many=True, read_only=True)
    attachments = QueryAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Query
        fields = '__all__'
        extra_kwargs = {
            'status': {'required': False},
            'priority': {'required': False},
            'tags': {'required': False},
            'contact_email': {'required': False},
            'contact_phone': {'required': False},
            'attachments': {'required': False}
        }