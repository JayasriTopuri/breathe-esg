from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from core.models import DataSource, ActivityRow, Tenant
from .parsers import parse_sap, parse_utility, parse_travel


class IngestFileView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        source_type = request.data.get('source_type')
        tenant_id = request.data.get('tenant_id')
        file = request.FILES.get('file')

        if not all([source_type, tenant_id, file]):
            return Response(
                {'error': 'source_type, tenant_id, and file are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return Response({'error': 'Tenant not found'}, status=status.HTTP_404_NOT_FOUND)

        data_source = DataSource.objects.create(
            tenant=tenant,
            source_type=source_type,
            ingest_mode='FILE_UPLOAD',
            raw_file=file,
            ingested_by=request.user if request.user.is_authenticated else None,
            status='PROCESSING',
        )

        try:
            if source_type == 'SAP':
                rows, errors = parse_sap(file, data_source)
            elif source_type == 'UTILITY':
                rows, errors = parse_utility(file, data_source)
            elif source_type == 'TRAVEL':
                rows, errors = parse_travel(file, data_source)
            else:
                data_source.status = 'FAILED'
                data_source.save()
                return Response({'error': 'Invalid source_type'}, status=status.HTTP_400_BAD_REQUEST)

            data_source.row_count = rows
            data_source.error_count = errors
            data_source.status = 'DONE'
            data_source.save()

            return Response({
                'message': 'File ingested successfully',
                'source_id': data_source.id,
                'rows_created': rows,
                'errors': errors,
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            data_source.status = 'FAILED'
            data_source.save()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DataSourceListView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        tenant_id = request.query_params.get('tenant_id')
        sources = DataSource.objects.all()
        if tenant_id:
            sources = sources.filter(tenant_id=tenant_id)

        data = [{
            'id': s.id,
            'source_type': s.source_type,
            'status': s.status,
            'row_count': s.row_count,
            'error_count': s.error_count,
            'ingested_at': s.ingested_at,
            'tenant': s.tenant.name,
        } for s in sources]

        return Response(data)