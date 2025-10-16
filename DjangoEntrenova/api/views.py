from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from accounts.models import PendenteAprovado
from .supabase_client import supabase

class AprovarPagamentoView (APIView):
    def post(self, request, cnpj_empresa):
        try:
            registro = PendenteAprovado.objects.get(cnpj_empresa=cnpj_empresa)
            registro.aprovar()
            supabase.table("pagamentos").update({"status": "aprovado"}).eq("cnpj_empresa", cnpj_empresa).execute()
            return Response({"message": "Pagamento aprovado"}, status=status.HTTP_200_OK)
        except PendenteAprovado.DoesNotExist:
            return Response ({"error": "Empresa não encontrada"}, status=status.HTTP_404_NOT_FOUND)