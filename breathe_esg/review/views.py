from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from core.models import ActivityRow, AuditLog


class ActivityRowListView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        tenant_id = request.query_params.get('tenant_id')
        row_status = request.query_params.get('status')
        category = request.query_params.get('category')
        scope = request.query_params.get('scope')

        rows = ActivityRow.objects.all().order_by('-created_at')

        if tenant_id:
            rows = rows.filter(tenant_id=tenant_id)
        if row_status:
            rows = rows.filter(status=row_status)
        if category:
            rows = rows.filter(category=category)
        if scope:
            rows = rows.filter(scope=scope)

        data = [{
            'id': r.id,
            'category': r.category,
            'scope': r.scope,
            'status': r.status,
            'activity_date': r.activity_date,
            'location': r.location,
            'vendor': r.vendor,
            'raw_quantity': r.raw_quantity,
            'raw_unit': r.raw_unit,
            'quantity_kwh': r.quantity_kwh,
            'quantity_liters': r.quantity_liters,
            'quantity_km': r.quantity_km,
            'flag_reason': r.flag_reason,
            'locked': r.locked,
            'notes': r.notes,
            'tenant': r.tenant.name,
            'data_source_id': r.data_source_id,
        } for r in rows]

        return Response(data)


class ReviewRowView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, row_id):
        try:
            row = ActivityRow.objects.get(id=row_id)
        except ActivityRow.DoesNotExist:
            return Response({'error': 'Row not found'}, status=status.HTTP_404_NOT_FOUND)

        if row.locked:
            return Response({'error': 'Row is locked for audit'}, status=status.HTTP_400_BAD_REQUEST)

        new_status = request.data.get('status')
        flag_reason = request.data.get('flag_reason', '')

        if new_status not in ['APPROVED', 'REJECTED', 'FLAGGED', 'PENDING']:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

        old_status = row.status
        row.status = new_status
        row.flag_reason = flag_reason
        row.reviewed_at = timezone.now()

        if new_status == 'APPROVED':
            row.locked = True

        row.save()

        AuditLog.objects.create(
            activity_row=row,
            changed_by=None,
            field_changed='status',
            old_value=old_status,
            new_value=new_status,
            action=f'Status changed to {new_status}',
        )

        return Response({
            'message': f'Row {new_status.lower()} successfully',
            'row_id': row.id,
            'locked': row.locked,
        })


class DashboardStatsView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        tenant_id = request.query_params.get('tenant_id')
        rows = ActivityRow.objects.all()

        if tenant_id:
            rows = rows.filter(tenant_id=tenant_id)

        data = {
            'total': rows.count(),
            'pending': rows.filter(status='PENDING').count(),
            'flagged': rows.filter(status='FLAGGED').count(),
            'approved': rows.filter(status='APPROVED').count(),
            'rejected': rows.filter(status='REJECTED').count(),
            'by_scope': {
                'scope1': rows.filter(scope=1).count(),
                'scope2': rows.filter(scope=2).count(),
                'scope3': rows.filter(scope=3).count(),
            },
            'by_category': {
                'FUEL': rows.filter(category='FUEL').count(),
                'ELECTRICITY': rows.filter(category='ELECTRICITY').count(),
                'FLIGHT': rows.filter(category='FLIGHT').count(),
                'HOTEL': rows.filter(category='HOTEL').count(),
                'GROUND_TRANSPORT': rows.filter(category='GROUND_TRANSPORT').count(),
                'PROCUREMENT': rows.filter(category='PROCUREMENT').count(),
            }
        }

        return Response(data)