"""parser for IEEE 802.15.4 frames"""
import struct
import struct

class IEEE802154Framer(object):
    frame_type_name = {0: "Beacon",
                       1: "Data",
                       2: "Acknowledgment",
                       3: "MAC command",
                      }

    def __init__(self, frame):
        self.frame = frame
        self.fc = self.parseheader()

    def parseheader(self):
        if len(self.frame) >= 2:
            framecontrol, = struct.unpack("<H", self.frame[:2])
            return framecontrol
        return None

    def frame_type(self):
        ftype = self.fc & 0x00007
        return self.frame_type_name[ftype]
    def sec_enabled(self):
        return (self.fc & 0x0008) == 0x0008
    def is_frame_pending(self):
        return (self.fc & 0x0010) == 0x0010
    def is_ack_requested(self):
        return (self.fc & 0x0020) == 0x0020
    def is_pan_id_compressed(self):
        return (self.fc & 0x0040) == 0x0040
    def frame_version(self):
        return (self.fc & 0x3000) >> 12
    def dst_addr_mode(self):
        return (self.fc & 0x0c00) >> 10
    def src_addr_mode(self):
        return (self.fc & 0xc000) >> 14
    def src_addr_size(self):
        mode = self.src_addr_mode()
        if mode == 0:
            return 0
        elif mode == 2:
            return 2
        elif mode == 3:
            return 8
        else:
            raise Exception()
    def dst_addr_size(self):
        mode = self.dst_addr_mode()
        if mode == 0:
            return 0
        elif mode == 2:
            return 2
        elif mode == 3:
            return 8
        else: # reserved
            raise Exception()

    def is_dst_panid_present(self):
        if self.src_addr_size() and self.dst_addr_size():
            if self.is_pan_id_compressed():
                return True
            else:
                return True
        elif self.src_addr_size():
            if self.is_pan_id_compressed():
                raise Exception()
            else:
                return False
        elif self.dst_addr_size():
            if self.is_pan_id_compressed():
                raise Exception()
            else:
                return True
        elif self.dst_addr_size() == 0 and self.src_addr_size() == 0:
            return False
        else:
            raise Exception()

    def is_src_panid_present(self):
        if self.src_addr_size() and self.dst_addr_size():
            if self.is_pan_id_compressed():
                return False
            else:
                return True
        elif self.src_addr_size():
            if self.is_pan_id_compressed():
                raise Exception()
            else:
                return True
        elif self.dst_addr_size():
            if self.is_pan_id_compressed():
                raise Exception()
            else:
                return False
        elif self.dst_addr_size() == 0 and self.src_addr_size() == 0:
            return False
        else:
            raise Exception()
    def compute_mac_payload_offset(self):
        offset = 3
        offset += 2 if self.is_src_panid_present() else 0
        offset += 2 if self.is_dst_panid_present() else 0
        offset += self.src_addr_size()
        offset += self.dst_addr_size()
        return offset
