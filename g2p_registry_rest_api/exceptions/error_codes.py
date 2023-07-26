from enum import Enum


class G2PErrorCodes(Enum):
    G2P_REQ_001 = "Invalid kind field."
    G2P_REQ_002 = "Field is mandatory."
    G2P_REQ_003 = "Group type Not Found"
    G2P_REQ_004 = "Member's kind not found."
    G2P_REQ_005 = "Invalid ID field."
    # Add more error codes and messages as needed

    def get_error_code(self):
        return self.name.replace("_", "-")

    def get_error_message(self):
        return self.value
