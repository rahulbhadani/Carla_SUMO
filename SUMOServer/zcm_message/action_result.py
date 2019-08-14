"""ZCM type definitions
This file automatically generated by zcm.
DO NOT MODIFY BY HAND!!!!
"""

try:
    import cStringIO.StringIO as BytesIO
except ImportError:
    from io import BytesIO
import struct

from Waypoint import Waypoint

class action_result(object):
    __slots__ = ["vehicle_id", "current_pos", "current_speed"]

    def __init__(self):
        self.vehicle_id = 0
        self.current_pos = Waypoint()
        self.current_speed = 0.0

    def encode(self):
        buf = BytesIO()
        buf.write(action_result._get_packed_fingerprint())
        self._encode_one(buf)
        return buf.getvalue()

    def _encode_one(self, buf):
        buf.write(struct.pack(">h", self.vehicle_id))
        assert self.current_pos._get_packed_fingerprint() == Waypoint._get_packed_fingerprint()
        self.current_pos._encode_one(buf)
        buf.write(struct.pack(">d", self.current_speed))

    def decode(data):
        if hasattr(data, 'read'):
            buf = data
        else:
            buf = BytesIO(data)
        if buf.read(8) != action_result._get_packed_fingerprint():
            raise ValueError("Decode error")
        return action_result._decode_one(buf)
    decode = staticmethod(decode)

    def _decode_one(buf):
        self = action_result()
        self.vehicle_id = struct.unpack(">h", buf.read(2))[0]
        self.current_pos = Waypoint._decode_one(buf)
        self.current_speed = struct.unpack(">d", buf.read(8))[0]
        return self
    _decode_one = staticmethod(_decode_one)

    _hash = None
    def _get_hash_recursive(parents):
        if action_result in parents: return 0
        newparents = parents + [action_result]
        tmphash = (0x954ba8e3e4656df+ Waypoint._get_hash_recursive(newparents)) & 0xffffffffffffffff
        tmphash  = (((tmphash<<1)&0xffffffffffffffff)  + ((tmphash>>63)&0x1)) & 0xffffffffffffffff
        return tmphash
    _get_hash_recursive = staticmethod(_get_hash_recursive)
    _packed_fingerprint = None

    def _get_packed_fingerprint():
        if action_result._packed_fingerprint is None:
            action_result._packed_fingerprint = struct.pack(">Q", action_result._get_hash_recursive([]))
        return action_result._packed_fingerprint
    _get_packed_fingerprint = staticmethod(_get_packed_fingerprint)

