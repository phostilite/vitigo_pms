from django.urls import path
from . import views

urlpatterns = [
    path('', views.PharmacyManagementView.as_view(), name='pharmacy_management'),
    path('purchase-order/new/', views.PurchaseOrderCreateView.as_view(), name='new_purchase_order'),
    path('medication/add/', views.MedicationCreateView.as_view(), name='add_medication'),
    path('stock/adjust/', views.StockAdjustmentView.as_view(), name='stock_adjustment'),
    path('low-stock/', views.LowStockItemsView.as_view(), name='low_stock_items'),
    path('medications/', views.AllMedicationsView.as_view(), name='all_medications'),
]