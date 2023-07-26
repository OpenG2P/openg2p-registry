from enum import Enum


class G2PErrorCodes(Enum):
    G2P_REQ_001 = "Invalid Kind Field."
    G2P_REQ_002 = "Field is Mandatory."
    G2P_REQ_003 = "Group Type Not Found"
    G2P_REQ_004 = "Member's Kind Not Found."
    G2P_REQ_005 = "Invalid ID Field."
    # Add more error codes and messages as needed

    def get_error_code(self):
        return self.name.replace("_", "-")

    def get_error_message(self):
        return self.value
