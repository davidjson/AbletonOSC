from typing import Tuple, Any
from .handler import AbletonOSCHandler

class ChainHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "chain"

    def init_api(self):
        def create_chain_callback(func, *args, include_ids: bool = False):
            def chain_callback(params: Tuple[Any]):
                track_index = int(params[0])
                device_index = int(params[1])
                chain_index = int(params[2])
                
                track = self.song.tracks[track_index]
                device = track.devices[device_index]
                
                # Check if device has chains
                if not hasattr(device, 'chains') or not device.chains:
                    return None
                
                if chain_index >= len(device.chains):
                    return None
                    
                chain = device.chains[chain_index]
                
                if include_ids:
                    rv = func(chain, *args, params[0:])
                else:
                    rv = func(chain, *args, params[3:])

                if rv is not None:
                    return (track_index, device_index, chain_index, *rv)

            return chain_callback

        # Properties that can be read
        properties_r = [
            "name",
            "mute",
            "solo",
            "color",
            "color_index"
        ]
        
        # Properties that can be read and written
        properties_rw = [
            "name",
            "mute",
            "solo"
        ]

        # Register read handlers
        for prop in properties_r:
            self.osc_server.add_handler("/live/chain/get/%s" % prop,
                                        create_chain_callback(self._get_property, prop))
            self.osc_server.add_handler("/live/chain/start_listen/%s" % prop,
                                        create_chain_callback(self._start_listen, prop))
            self.osc_server.add_handler("/live/chain/stop_listen/%s" % prop,
                                        create_chain_callback(self._stop_listen, prop))
        
        # Register write handlers
        for prop in properties_rw:
            self.osc_server.add_handler("/live/chain/set/%s" % prop,
                                        create_chain_callback(self._set_property, prop))

        # Add chain count to device handler
        def get_num_chains(params: Tuple[Any]):
            track_index = int(params[0])
            device_index = int(params[1])
            
            track = self.song.tracks[track_index]
            device = track.devices[device_index]
            
            if hasattr(device, 'chains'):
                return (track_index, device_index, len(device.chains))
            else:
                return (track_index, device_index, 0)
        
        self.osc_server.add_handler("/live/device/get/num_chains", get_num_chains)
        
        # Get devices in a chain
        def get_chain_num_devices(params: Tuple[Any]):
            track_index = int(params[0])
            device_index = int(params[1])
            chain_index = int(params[2])
            
            track = self.song.tracks[track_index]
            device = track.devices[device_index]
            
            if hasattr(device, 'chains') and chain_index < len(device.chains):
                chain = device.chains[chain_index]
                if hasattr(chain, 'devices'):
                    return (track_index, device_index, chain_index, len(chain.devices))
            
            return (track_index, device_index, chain_index, 0)
        
        self.osc_server.add_handler("/live/chain/get/num_devices", get_chain_num_devices)
        
        # Get device name in chain
        def get_chain_device_name(params: Tuple[Any]):
            track_index = int(params[0])
            device_index = int(params[1])
            chain_index = int(params[2])
            chain_device_index = int(params[3])
            
            track = self.song.tracks[track_index]
            device = track.devices[device_index]
            
            if hasattr(device, 'chains') and chain_index < len(device.chains):
                chain = device.chains[chain_index]
                if hasattr(chain, 'devices') and chain_device_index < len(chain.devices):
                    chain_device = chain.devices[chain_device_index]
                    return (track_index, device_index, chain_index, chain_device_index, chain_device.name)
            
            return None
        
        self.osc_server.add_handler("/live/chain/device/get/name", get_chain_device_name)