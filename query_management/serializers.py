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

class SimpleQuerySerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta:
        model = Query
        fields = ['first_name', 'last_name']

    def create(self, validated_data):
        # Extract first_name and last_name
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')

        # Create query with default values
        query = Query.objects.create(
            subject=f"Query from {first_name} {last_name}",
            description=f"Automatically created query for {first_name} {last_name}",
            source='WEBSITE',  # Default source
            priority='B',      # Default priority (Medium)
            status='NEW',      # Default status
            contact_email=f"{first_name.lower()}.{last_name.lower()}@example.com",  # Sample email
            is_anonymous=False
        )
        return query