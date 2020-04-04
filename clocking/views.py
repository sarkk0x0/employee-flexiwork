from datetime import datetime

from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ParseError, NotFound

from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import ClockType, Clock
from .serializers import ClockTypeSerializer, ClockSerializer
# Create your views here.

class ClockTypeList(generics.ListCreateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = ClockType.objects.all()
    serializer_class = ClockTypeSerializer


class ClockList(generics.ListCreateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Clock.objects.all()
    serializer_class = ClockSerializer

    def perform_create(self, serializer):
        employee_id = serializer.validated_data.get('employee').pk
        #Check if employee does not have clock-in object for the day
        _date = datetime.date(datetime.now())
        clock_obj_exist = self.get_queryset().filter(clock_in_timestamp__date=_date, employee__id=employee_id).exists()
        if not clock_obj_exist:
            serializer.save()
        else:
            raise ParseError('This employee already has a registered clock-in for today!')


class CheckClockForEmployee(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        
        _date = datetime.date(datetime.now())
        try:
            clock_obj = Clock.objects.get(clock_in_timestamp__date=_date, employee__id=pk)
        except ObjectDoesNotExist:
            raise NotFound('This Employee has not clocked in today!')
    
        serializer = ClockSerializer(clock_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EmployeeClockOut(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        
        current_datetime = datetime.now()
        _date = datetime.date(current_datetime)
        try:
            clock_obj = Clock.objects.get(clock_in_timestamp__date=_date, employee__id=pk)
        except ObjectDoesNotExist:
            raise NotFound("This Employee has not clocked in today and hence can't clock out!")
        
        clock_obj.clock_out_timestamp = current_datetime
        clock_obj.valid_attendance = True
        clock_obj.save()

        serializer = ClockSerializer(clock_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)