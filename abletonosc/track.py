from typing import Tuple, Any, Callable, Optional
from .handler import AbletonOSCHandler


class TrackHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "track"

    def init_api(self):
        def create_track_callback(func: Callable,
                                  *args,
                                  include_track_id: bool = False):
            def track_callback(params: Tuple[Any]):
                if params[0] == "*":
                    track_indices = list(range(len(self.song.tracks)))
                else:
                    track_indices = [int(params[0])]

                for track_index in track_indices:
                    track = self.song.tracks[track_index]
                    if include_track_id:
                        rv = func(track, *args, tuple([track_index] + params[1:]))
                    else:
                        rv = func(track, *args, tuple(params[1:]))

                    if rv is not None:
                        return (track_index, *rv)

            return track_callback

        methods = [
            "create_audio_clip",
            "create_midi_clip",
            "create_take_lane",
            "delete_device",
            "duplicate_clip_slot",
            "duplicate_clip_to_arrangement",
            "jump_in_running_session_clip",
            "stop_all_clips"
        ]
        properties_r = [
            "can_be_armed",
            "can_be_frozen",
            "can_show_chains",
            "fired_slot_index",
            "has_audio_input",
            "has_audio_output",
            "has_midi_input",
            "has_midi_output",
            "is_foldable",
            "is_frozen",
            "is_grouped",
            "is_part_of_selection",
            "is_visible",
            "muted_via_solo",
            "output_meter_level",
            "output_meter_left",
            "output_meter_right",
            "performance_impact",
            "playing_slot_index"
        ]
        properties_rw = [
            "arm",
            "back_to_arranger",
            "color",
            "color_index",
            "current_monitoring_state",
            "fold_state",
            "implicit_arm",
            "input_meter_left",
            "input_meter_level",
            "input_meter_right",
            "is_showing_chains",
            "mute",
            "name",
            "solo"
        ]

        for method in methods:
            self.osc_server.add_handler("/live/track/%s" % method,
                                        create_track_callback(self._call_method, method))

        for prop in properties_r + properties_rw:
            self.osc_server.add_handler("/live/track/get/%s" % prop,
                                        create_track_callback(self._get_property, prop))
            self.osc_server.add_handler("/live/track/start_listen/%s" % prop,
                                        create_track_callback(self._start_listen, prop, include_track_id=True))
            self.osc_server.add_handler("/live/track/stop_listen/%s" % prop,
                                        create_track_callback(self._stop_listen, prop, include_track_id=True))
        for prop in properties_rw:
            self.osc_server.add_handler("/live/track/set/%s" % prop,
                                        create_track_callback(self._set_property, prop))

        #--------------------------------------------------------------------------------
        # Volume, panning and send are properties of the track's mixer_device so
        # can't be formulated as normal callbacks that reference properties of track.
        #--------------------------------------------------------------------------------
        mixer_properties_rw = ["volume", "panning"]
        for prop in mixer_properties_rw:
            self.osc_server.add_handler("/live/track/get/%s" % prop,
                                        create_track_callback(self._get_mixer_property, prop))
            self.osc_server.add_handler("/live/track/set/%s" % prop,
                                        create_track_callback(self._set_mixer_property, prop))
            self.osc_server.add_handler("/live/track/start_listen/%s" % prop,
                                        create_track_callback(self._start_mixer_listen, prop, include_track_id=True))
            self.osc_server.add_handler("/live/track/stop_listen/%s" % prop,
                                        create_track_callback(self._stop_mixer_listen, prop, include_track_id=True))

        # Still need to fix these
        # Might want to find a better approach that unifies volume and sends
        def track_get_send(track, params: Tuple[Any] = ()):
            send_id, = params
            return send_id, track.mixer_device.sends[send_id].value

        def track_set_send(track, params: Tuple[Any] = ()):
            send_id, value = params
            track.mixer_device.sends[send_id].value = value

        self.osc_server.add_handler("/live/track/get/send", create_track_callback(track_get_send))
        self.osc_server.add_handler("/live/track/set/send", create_track_callback(track_set_send))

        def track_delete_clip(track, params: Tuple[Any]):
            clip_index, = params
            track.clip_slots[clip_index].delete_clip()

        self.osc_server.add_handler("/live/track/delete_clip", create_track_callback(track_delete_clip))

        def track_get_clip_names(track, _):
            return tuple(clip_slot.clip.name if clip_slot.clip else None for clip_slot in track.clip_slots)

        def track_get_clip_lengths(track, _):
            return tuple(clip_slot.clip.length if clip_slot.clip else None for clip_slot in track.clip_slots)

        def track_get_clip_colors(track, _):
            return tuple(clip_slot.clip.color if clip_slot.clip else None for clip_slot in track.clip_slots)

        def track_get_arrangement_clip_names(track, _):
            try:
                return tuple(clip.name for clip in track.arrangement_clips)
            except RuntimeError:
                return tuple()  # Return empty tuple for group/return tracks

        def track_get_arrangement_clip_lengths(track, _):
            try:
                return tuple(clip.length for clip in track.arrangement_clips)
            except RuntimeError:
                return tuple()  # Return empty tuple for group/return tracks

        def track_get_arrangement_clip_start_times(track, _):
            try:
                return tuple(clip.start_time for clip in track.arrangement_clips)
            except RuntimeError:
                return tuple()  # Return empty tuple for group/return tracks
        
        def track_get_arrangement_clip_end_times(track, _):
            try:
                return tuple(clip.end_time for clip in track.arrangement_clips)
            except RuntimeError:
                return tuple()  # Return empty tuple for group/return tracks
        
        def track_get_arrangement_clip_muted_states(track, _):
            try:
                return tuple(clip.muted for clip in track.arrangement_clips)
            except RuntimeError:
                return tuple()  # Return empty tuple for group/return tracks

        """
        Returns a list of clip properties, or Nil if clip is empty
        """
        self.osc_server.add_handler("/live/track/get/clips/name", create_track_callback(track_get_clip_names))
        self.osc_server.add_handler("/live/track/get/clips/length", create_track_callback(track_get_clip_lengths))
        self.osc_server.add_handler("/live/track/get/clips/color", create_track_callback(track_get_clip_colors))
        self.osc_server.add_handler("/live/track/get/arrangement_clips/name", create_track_callback(track_get_arrangement_clip_names))
        self.osc_server.add_handler("/live/track/get/arrangement_clips/length", create_track_callback(track_get_arrangement_clip_lengths))
        self.osc_server.add_handler("/live/track/get/arrangement_clips/start_time", create_track_callback(track_get_arrangement_clip_start_times))
        self.osc_server.add_handler("/live/track/get/arrangement_clips/end_time", create_track_callback(track_get_arrangement_clip_end_times))
        self.osc_server.add_handler("/live/track/get/arrangement_clips/muted", create_track_callback(track_get_arrangement_clip_muted_states))

        def track_get_num_devices(track, _):
            return len(track.devices),

        def track_get_device_names(track, _):
            return tuple(device.name for device in track.devices)

        def track_get_device_types(track, _):
            return tuple(device.type for device in track.devices)

        def track_get_device_class_names(track, _):
            return tuple(device.class_name for device in track.devices)

        def track_get_device_can_have_chains(track, _):
            return tuple(device.can_have_chains for device in track.devices)

        """
         - name: the device's human-readable name
         - type: 0 = audio_effect, 1 = instrument, 2 = midi_effect
         - class_name: e.g. Operator, Reverb, AuPluginDevice, PluginDevice, InstrumentGroupDevice
        """
        self.osc_server.add_handler("/live/track/get/num_devices", create_track_callback(track_get_num_devices))
        self.osc_server.add_handler("/live/track/get/devices/name", create_track_callback(track_get_device_names))
        self.osc_server.add_handler("/live/track/get/devices/type", create_track_callback(track_get_device_types))
        self.osc_server.add_handler("/live/track/get/devices/class_name", create_track_callback(track_get_device_class_names))
        self.osc_server.add_handler("/live/track/get/devices/can_have_chains", create_track_callback(track_get_device_can_have_chains))

        #--------------------------------------------------------------------------------
        # Track: Output routing.
        # An output route has a type (e.g. "Ext. Out") and a channel (e.g. "1/2").
        # Since Live 10, both of these need to be set by reference to the appropriate
        # item in the available_output_routing_types vector.
        #--------------------------------------------------------------------------------
        def track_get_available_output_routing_types(track, _):
            return tuple([routing_type.display_name for routing_type in track.available_output_routing_types])
        def track_get_available_output_routing_channels(track, _):
            return tuple([routing_channel.display_name for routing_channel in track.available_output_routing_channels])
        def track_get_output_routing_type(track, _):
            return track.output_routing_type.display_name,
        def track_set_output_routing_type(track, params):
            type_name = str(params[0])
            for routing_type in track.available_output_routing_types:
                if routing_type.display_name == type_name:
                    track.output_routing_type = routing_type
                    return
            self.logger.warning("Couldn't find output routing type: %s" % type_name)
        def track_get_output_routing_channel(track, _):
            return track.output_routing_channel.display_name,
        def track_set_output_routing_channel(track, params):
            channel_name = str(params[0])
            for channel in track.available_output_routing_channels:
                if channel.display_name == channel_name:
                    track.output_routing_channel = channel
                    return
            self.logger.warning("Couldn't find output routing channel: %s" % channel_name)

        self.osc_server.add_handler("/live/track/get/available_output_routing_types", create_track_callback(track_get_available_output_routing_types))
        self.osc_server.add_handler("/live/track/get/available_output_routing_channels", create_track_callback(track_get_available_output_routing_channels))
        self.osc_server.add_handler("/live/track/get/output_routing_type", create_track_callback(track_get_output_routing_type))
        self.osc_server.add_handler("/live/track/set/output_routing_type", create_track_callback(track_set_output_routing_type))
        self.osc_server.add_handler("/live/track/get/output_routing_channel", create_track_callback(track_get_output_routing_channel))
        self.osc_server.add_handler("/live/track/set/output_routing_channel", create_track_callback(track_set_output_routing_channel))

        #--------------------------------------------------------------------------------
        # Track: Input routing.
        #--------------------------------------------------------------------------------
        def track_get_available_input_routing_types(track, _):
            return tuple([routing_type.display_name for routing_type in track.available_input_routing_types])
        def track_get_available_input_routing_channels(track, _):
            return tuple([routing_channel.display_name for routing_channel in track.available_input_routing_channels])
        def track_get_input_routing_type(track, _):
            return track.input_routing_type.display_name,
        def track_set_input_routing_type(track, params):
            type_name = str(params[0])
            for routing_type in track.available_input_routing_types:
                if routing_type.display_name == type_name:
                    track.input_routing_type = routing_type
                    return
            self.logger.warning("Couldn't find input routing type: %s" % type_name)
        def track_get_input_routing_channel(track, _):
            return track.input_routing_channel.display_name,
        def track_set_input_routing_channel(track, params):
            channel_name = str(params[0])
            for channel in track.available_input_routing_channels:
                if channel.display_name == channel_name:
                    track.input_routing_channel = channel
                    return
            self.logger.warning("Couldn't find input routing channel: %s" % channel_name)

        self.osc_server.add_handler("/live/track/get/available_input_routing_types", create_track_callback(track_get_available_input_routing_types))
        self.osc_server.add_handler("/live/track/get/available_input_routing_channels", create_track_callback(track_get_available_input_routing_channels))
        self.osc_server.add_handler("/live/track/get/input_routing_type", create_track_callback(track_get_input_routing_type))
        self.osc_server.add_handler("/live/track/set/input_routing_type", create_track_callback(track_set_input_routing_type))
        self.osc_server.add_handler("/live/track/get/input_routing_channel", create_track_callback(track_get_input_routing_channel))
        self.osc_server.add_handler("/live/track/set/input_routing_channel", create_track_callback(track_set_input_routing_channel))

        #--------------------------------------------------------------------------------
        # Track: Additional properties for collections
        #--------------------------------------------------------------------------------
        def track_get_num_clip_slots(track, _):
            return len(track.clip_slots),
        
        def track_get_num_arrangement_clips(track, _):
            return len(track.arrangement_clips),
        
        def track_get_group_track_name(track, _):
            if hasattr(track, 'group_track') and track.group_track:
                return track.group_track.name,
            return None,

        def track_get_group_track_index(track, _):
            """Get the index of the parent group track"""
            if hasattr(track, 'group_track') and track.group_track:
                # Find the index of the group track
                for i, t in enumerate(self.song.tracks):
                    if t == track.group_track:
                        return i,
            return -1,

        def track_get_num_take_lanes(track, _):
            if hasattr(track, 'take_lanes'):
                return len(track.take_lanes),
            return 0,

        self.osc_server.add_handler("/live/track/get/num_clip_slots", create_track_callback(track_get_num_clip_slots))
        self.osc_server.add_handler("/live/track/get/num_arrangement_clips", create_track_callback(track_get_num_arrangement_clips))
        self.osc_server.add_handler("/live/track/get/group_track", create_track_callback(track_get_group_track_name))
        self.osc_server.add_handler("/live/track/get/group_track_index", create_track_callback(track_get_group_track_index))
        self.osc_server.add_handler("/live/track/get/num_take_lanes", create_track_callback(track_get_num_take_lanes))

        #--------------------------------------------------------------------------------
        # Track.View: Properties and methods for track view
        #--------------------------------------------------------------------------------
        def track_view_get_device_insert_mode(track, _):
            """Get the device insert mode (0=end, 1=left of selected, 2=right of selected)"""
            if hasattr(track, 'view') and hasattr(track.view, 'device_insert_mode'):
                return track.view.device_insert_mode,
            return 0,  # Default to end if not available
        
        def track_view_set_device_insert_mode(track, params):
            """Set the device insert mode (0=end, 1=left of selected, 2=right of selected)"""
            mode = int(params[0])
            if hasattr(track, 'view') and hasattr(track.view, 'device_insert_mode'):
                track.view.device_insert_mode = mode
                self.logger.info(f"Set device_insert_mode to {mode} for track")
            else:
                self.logger.warning("Track.view.device_insert_mode not available")
        
        def track_view_get_selected_device(track, _):
            """Get the currently selected device on the track"""
            if hasattr(track, 'view') and hasattr(track.view, 'selected_device'):
                if track.view.selected_device:
                    try:
                        device_index = list(track.devices).index(track.view.selected_device)
                        return device_index,
                    except ValueError:
                        pass
            return -1,  # No device selected
        
        def track_view_select_instrument(track, _):
            """Select the track's instrument or first device"""
            if hasattr(track, 'view') and hasattr(track.view, 'select_instrument'):
                result = track.view.select_instrument()
                self.logger.info(f"Called select_instrument, result: {result}")
                return result,
            else:
                self.logger.warning("Track.view.select_instrument not available")
                return 0,
        
        def track_view_select_device(track, params):
            """Select a specific device by index on the track"""
            if not params:
                self.logger.warning("No device index provided")
                return 0,
            
            device_index = int(params[0])
            
            # First check if track has devices
            if not hasattr(track, 'devices') or device_index >= len(track.devices):
                self.logger.warning(f"Device index {device_index} out of range")
                return 0,
            
            # Get the device object
            device = track.devices[device_index]
            
            # Use the song's view to select the device (the proper API way)
            if hasattr(self.song.view, 'select_device'):
                self.song.view.select_device(device)
                self.logger.info(f"Selected device at index {device_index} using song.view.select_device")
                return 1,
            else:
                self.logger.warning("song.view.select_device not available")
                return 0,
        
        def track_view_get_is_collapsed(track, _):
            """Get whether the track is collapsed in Arrangement View"""
            if hasattr(track, 'view') and hasattr(track.view, 'is_collapsed'):
                return track.view.is_collapsed,
            return 0,
        
        def track_view_set_is_collapsed(track, params):
            """Set whether the track is collapsed in Arrangement View"""
            collapsed = int(params[0])
            if hasattr(track, 'view') and hasattr(track.view, 'is_collapsed'):
                track.view.is_collapsed = collapsed
                self.logger.info(f"Set is_collapsed to {collapsed} for track")
            else:
                self.logger.warning("Track.view.is_collapsed not available")

        # Register track.view handlers
        self.osc_server.add_handler("/live/track/view/get/device_insert_mode", 
                                   create_track_callback(track_view_get_device_insert_mode))
        self.osc_server.add_handler("/live/track/view/set/device_insert_mode", 
                                   create_track_callback(track_view_set_device_insert_mode))
        self.osc_server.add_handler("/live/track/view/get/selected_device", 
                                   create_track_callback(track_view_get_selected_device))
        self.osc_server.add_handler("/live/track/view/select_instrument", 
                                   create_track_callback(track_view_select_instrument))
        self.osc_server.add_handler("/live/track/view/select_device", 
                                   create_track_callback(track_view_select_device))
        self.osc_server.add_handler("/live/track/view/get/is_collapsed", 
                                   create_track_callback(track_view_get_is_collapsed))
        self.osc_server.add_handler("/live/track/view/set/is_collapsed", 
                                   create_track_callback(track_view_set_is_collapsed))

    def _set_mixer_property(self, target, prop, params: Tuple) -> None:
        parameter_object = getattr(target.mixer_device, prop)
        self.logger.info("Setting property for %s: %s (new value %s)" % (self.class_identifier, prop, params[0]))
        parameter_object.value = params[0]

    def _get_mixer_property(self, target, prop, params: Optional[Tuple] = ()) -> Tuple[Any]:
        parameter_object = getattr(target.mixer_device, prop)
        self.logger.info("Getting property for %s: %s = %s" % (self.class_identifier, prop, parameter_object.value))
        return parameter_object.value,

    def _start_mixer_listen(self, target, prop, params: Optional[Tuple] = ()) -> None:
        parameter_object = getattr(target.mixer_device, prop)
        def property_changed_callback():
            value = parameter_object.value
            self.logger.info("Property %s changed of %s %s: %s" % (prop, self.class_identifier, str(params), value))
            osc_address = "/live/%s/get/%s" % (self.class_identifier, prop)
            self.osc_server.send(osc_address, (*params, value,))

        listener_key = (prop, tuple(params))
        if listener_key in self.listener_functions:
            self._stop_mixer_listen(target, prop, params)

        self.logger.info("Adding listener for %s %s, property: %s" % (self.class_identifier, str(params), prop))

        parameter_object.add_value_listener(property_changed_callback)
        self.listener_functions[listener_key] = property_changed_callback
        #--------------------------------------------------------------------------------
        # Immediately send the current value
        #--------------------------------------------------------------------------------
        property_changed_callback()

    def _stop_mixer_listen(self, target, prop, params: Optional[Tuple[Any]] = ()) -> None:
        parameter_object = getattr(target.mixer_device, prop)
        listener_key = (prop, tuple(params))
        if listener_key in self.listener_functions:
            self.logger.info("Removing listener for %s %s, property %s" % (self.class_identifier, str(params), prop))
            listener_function = self.listener_functions[listener_key]
            parameter_object.remove_value_listener(listener_function)
            del self.listener_functions[listener_key]
        else:
            self.logger.warning("No listener function found for property: %s (%s)" % (prop, str(params)))
