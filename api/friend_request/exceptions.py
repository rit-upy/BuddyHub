from rest_framework.exceptions import Throttled
from rest_framework.views import exception_handler
from rest_framework.response import Response

def throttle_exception(exception, context):
    response = exception_handler(exc=exception, context=context)

    if isinstance(exception, Throttled):
        detail = exception.detail.split(' ')
        time = detail[-2]
        time_unit = detail[-1]
        response_data = {
            'message' : 'You are allowed to send only 3 requests per minute.', 
            'available_in' :f'{time} {time_unit}'  
        }
        return Response(response_data, status=exception.status_code)
    return response #if all is good