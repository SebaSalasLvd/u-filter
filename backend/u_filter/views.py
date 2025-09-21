from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .modelo_bert import bert_pipeline_test

#Ignorar era para testear
class HelloView(APIView):
    def get(self, request):
        return Response({"message": "Hello from Django REST Framework!"})

#La vista de BERT esto sera nuestra punto de llamada al modelo para devolver la respuesta al front
class BERTView(APIView):
    def post(self, request):
        text = request.data.get("text", None) #Esto se cambia despues segun como hagamos el front
        if not text:
            return Response({"error": "No text provided"}, status=status.HTTP_400_BAD_REQUEST)

        result = bert_pipeline_test(text)
        return Response({"input": text, "classification": result})