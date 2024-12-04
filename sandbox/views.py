# views.py
from django.shortcuts import render
from body_mapping.models.base import BodyModel
from body_mapping.models.coordinates import BodyImage

def image_carousel(request):
    selected_gender = request.GET.get('gender', 'M')  # Default to male
    
    # Get the body model for selected gender
    body_model = BodyModel.objects.filter(
        gender__code=selected_gender,
        is_active=True
    ).first()
    
    # Get all images for this model
    if body_model:
        images = BodyImage.objects.filter(
            body_model=body_model
        ).select_related('view').order_by('view__display_order')
        
        image_data = [
            {
                'id': img.id,
                'src': img.image.url,
                'alt': f'{img.body_model.gender.name} - {img.view.name}',
                'view_code': img.view.code
            } for img in images
        ]
    else:
        image_data = []
    
    context = {
        'images': image_data,
        'selected_gender': selected_gender,
    }
    
    return render(request, 'sandbox/image_coordinates.html', context)