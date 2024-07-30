
from rest_framework import generics,status
from .models import Friends
from authentication.models import User
from .serializers import AcceptedRequestUsersSerializer,SearchUsersSerializer,RequestSerializer, SendRequestSerializer, ReceivedRequestUserSerializer
from rest_framework.response import Response
from rest_framework import viewsets
from django.db.models import Q
from .paginators import SearchUserPagination
from rest_framework.throttling import ScopedRateThrottle



# Create your views here.
class ListUsers(generics.ListAPIView):
    
    serializer_class = AcceptedRequestUsersSerializer

    def get(self, request, *args, **kwargs):
        user = request.user
        pending_status = kwargs.get('pending_status')        

        if not pending_status:
            return Response('Status not provided', status=status.HTTP_400_BAD_REQUEST)
        elif pending_status.lower() == 'accepted':
            friends = Friends.objects.filter(user = user, pending = False)            
        elif pending_status.lower() == 'pending':
            self.serializer_class = ReceivedRequestUserSerializer
            friends = Friends.objects.filter(friend = user, pending = True) 
        else:
            return Response('Wrong status request!', status=status.HTTP_400_BAD_REQUEST)
        
        
        if len(friends) == 0:
            return Response(f'You have no {pending_status} friend requests', status=status.HTTP_200_OK)
        self.queryset = friends
        
        return super().get(request, *args, **kwargs)




class SearchAPIView(generics.ListAPIView):
    serializer_class = SearchUsersSerializer
    pagination_class = SearchUserPagination
    
    def get_queryset(self):
        search_email = self.request.query_params.get('email', None)

        if search_email is not None:    
            return User.objects.filter(email__iexact = search_email)
        
        name = self.request.query_params.get('name', None)
        
        if name is not None:
            
            return User.objects.filter(Q(first_name__icontains=name) | Q(last_name__icontains=name))
        return Response('Please enter the email or the name field.',\
                             status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class FriendRequest(viewsets.ModelViewSet):
    
    serializer_class = RequestSerializer

    def update(self, request, *args, **kwargs):
        user = request.user
        friend = request.data['friend']

        if Friends.objects.filter(user = user, friend = friend).exists():
            return Response('You cannot accept your own friend request. You must wait for the other person.'
                            , status=status.HTTP_400_BAD_REQUEST)
        try:
            friend = Friends.objects.get(user = friend, friend = user, pending = True) #accepting request
        except Friends.DoesNotExist:
            return Response('The request seems to be wrong. Check again', status=status.HTTP_400_BAD_REQUEST)
        friend.pending = False
        friend.save()
        return Response('Friend request is accepted.', status=status.HTTP_200_OK)
    
    

    def destroy(self, request, *args, **kwargs): #reject
        user = request.user
        friend_id = request.data['friend']
        if user.id == friend_id:
            return Response('User and friend are the same', status=status.HTTP_400_BAD_REQUEST)
        

        try:
            friend = Friends.objects.get(user__id = friend_id , friend = user )
        except Friends.DoesNotExist:
            return Response('Friend request does not exist.', status=status.HTTP_400_BAD_REQUEST)
        
        if friend.pending is False:
            return Response('Request is already accepted and can\'t be deleted', status=status.HTTP_400_BAD_REQUEST)
        
        friend.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SendRequestView(generics.CreateAPIView):
    serializer_class = SendRequestSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'send'
