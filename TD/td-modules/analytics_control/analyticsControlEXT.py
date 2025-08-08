# pylint: disable=missing-docstring,logging-fstring-interpolation
import json
import base64
import uuid
from datetime import datetime
from vvox_tdtools.base import BaseEXT
# from vvox_tdtools.parhelper import ParTemplate
try:
    # import td
    from td import OP # type: ignore
    # TDJ = op.TDModules.mod.TDJSON
    # TDF = op.TDModules.mod.TDFunctions
except ModuleNotFoundError:
    from vvox_tdtools.td_mock import OP  #pylint: disable=ungrouped-imports 
    # from tdconfig import TDJSON as TDJ
    # from tdconfig import TDFunctions as TDF


class AnalyticsControlEXT(BaseEXT):
    def __init__(self, myop: OP) -> None:
        BaseEXT.__init__(self, myop, par_callback_on=True)
        self.Me.par.opshortcut = "analytics_control"
        self.Mixpaneltoken = "8f1255a44f049242c9e18330c539d156"  # Default Mixpanel token
        self.event_name = "Photo Booth Start"
        pass

    def OnInit(self):
        # return False if initialization fails
        return True

    def Send_mixpanel_event(self):
        properties = {
            'event_type': 'photo_booth_start',
            'session_id': f"photobooth_{int(datetime.now().timestamp())}",
            'timestamp': datetime.now().isoformat(),
            'platform': 'Touchdesigner',
            'source': 'Cadillac Photo Booth'
        }
        # Default distinct_id if not provided
        distinct_id = str(uuid.uuid4())
        
        
        # Add required token to properties
        properties['token'] = self.Mixpaneltoken
        properties['time'] = int(datetime.now().timestamp())
        
        # Prepare the event data
        event_data = {
            'event': self.event_name,
            'properties': properties
        }
        
        # If distinct_id is provided, add it to properties
        if distinct_id:
            event_data['properties']['distinct_id'] = distinct_id
        
        try:
            # Mixpanel expects base64 encoded JSON
            data_json = json.dumps(event_data)
            data_b64 = base64.b64encode(data_json.encode('utf-8')).decode('utf-8')
            
            # Send to Mixpanel HTTP API
            url = 'https://api.mixpanel.com/track'
            payload = {'data': data_b64}

            self.Me.op("webclient1").request(url,"POST", data=payload)
            # if response.status_code == 200 and response.text == '1':
            #     print("✅ Event sent successfully to Mixpanel!")
            #     return True
            # else:
            #     print(f"❌ Failed to send event. Status: {response.status_code}, Response: {response.text}")
            #     return False
                
        except Exception as e:
            print(f"❌ Error sending event to Mixpanel: {str(e)}")
            return False

    def HandleResponse(self, statusCode, headerDict, data, id):
        """
        Handle the response from the web client.
        
        Args:
            statusCode (dict): The status code of the response.
            headerDict (dict): The header of the response.
            data (str): The data of the response.
            id (str): The request's unique identifier.
        """
        response_str = (f"Response received: {statusCode}, {headerDict}, {data}, {id}")
        self.Logger.debug(response_str)
        # Process the response as needed
        pass

    # Below is an example of a parameter callback. Simply create a method that starts with "_on" and then the name of the parameter.

    # def _onExampletoggle(self, par):
    #     self.Logger.debug(f"_onExampleToggle - val: {par.eval()}")
    #     pass

    # Below is an example of creating an event loop by overriding the OnFrameStart method.

    # def OnFrameStart(self, frame: int):
    #     if frame % 60 == 0:
    #         self.OnEventLoop1()
    #     return 

    # def OnEventLoop1(self):
    #     self.Print('every second')
    #     pass


