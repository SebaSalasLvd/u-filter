from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .modelo_bert import bert_pipeline_test

class HelloView(APIView):
    def get(self, request):
        return Response({"message": "Hello from Django REST Framework!"})

class BERTView(APIView):
    def post(self, request):
        text = request.data.get("text", None)
        if not text:
            return Response({"error": "No text provided"}, status=status.HTTP_400_BAD_REQUEST)

        result = bert_pipeline_test(text)
        return Response({"input": text, "classification": result})