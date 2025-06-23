
import json

try:
    # import td
    from td import OP, op, parent
    # TDJ = op.TDModules.mod.TDJSON
    # TDF = op.TDModules.mod.TDFunctions
except ModuleNotFoundError:
    from vvox_tdtools.td_mock import OP, parent  #pylint: disable=ungrouped-imports
    # from tdconfig import TDJSON as TDJ
    # from tdconfig import TDFunctions as TDF


# return the response dictionary
def onHTTPRequest(webServerDAT, request, response): #pylint: disable=unused-argument
    # get the uri from the request header
    uri = request['uri']

    if uri == '/':
        response['statusCode'] = 200 # OK
        response['statusReason'] = 'OK'
        response['data'] = op('index').text
    elif uri == '/metrics':
        # print('metrics request')
        # print('server address', request['serverAddress'])
        response['statusCode'] = 200 # OK
        response['statusReason'] = 'OK'
        response['data'] = parent().GenerateResponse().encode()
    # else just respond with 200/OK
    else:
        response['statusCode'] = 200 # OK
        response['statusReason'] = 'OK'

    return response

# def onWebSocketOpen(webServerDAT, client):
#     return

# def onWebSocketClose(webServerDAT, client):
#     return

# def onWebSocketReceiveText(webServerDAT, client, data):
#     return

# def onWebSocketReceiveBinary(webServerDAT, client, data):
#     # webServerDAT.webSocketSendBinary(client, data)
#     return

# def onServerStart(webServerDAT):
#     return

# def onServerStop(webServerDAT):
#     return


# me - this DAT.
# webServerDAT - the connected Web Server DAT
# request - A dictionary of the request fields. The dictionary will always contain the below entries, plus any additional entries dependent on the contents of the request
# 		'method' - The HTTP method of the request (ie. 'GET', 'PUT').
# 		'uri' - The client's requested URI path. If there are parameters in the URI then they will be located under the 'pars' key in the request dictionary.
#		'pars' - The query parameters.
# 		'clientAddress' - The client's address.
# 		'serverAddress' - The server's address.
# 		'data' - The data of the HTTP request.
# response - A dictionary defining the response, to be filled in during the request method. Additional fields not specified below can be added (eg. response['content-type'] = 'application/json').
# 		'statusCode' - A valid HTTP status code integer (ie. 200, 401, 404). Default is 404.
# 		'statusReason' - The reason for the above status code being returned (ie. 'Not Found.').
# 		'data' - The data to send back to the client. If displaying a web-page, any HTML would be put here.
