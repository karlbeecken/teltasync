"""Teltonika API error codes and their descriptions."""

from enum import IntEnum
from typing import Dict


class TeltonikaErrorCode(IntEnum):
    """Teltonika API error codes as defined in the API documentation."""

    # General API errors (100-119)
    RESPONSE_NOT_IMPLEMENTED = 100
    NO_ACTION_PROVIDED = 101
    PROVIDED_ACTION_NOT_AVAILABLE = 102
    INVALID_OPTIONS = 103
    UCI_GET_ERROR = 104
    UCI_DELETE_ERROR = 105
    UCI_CREATE_ERROR = 106
    INVALID_STRUCTURE = 107
    SECTION_CREATION_NOT_ALLOWED = 108
    NAME_ALREADY_USED = 109
    NAME_NOT_PROVIDED = 110
    DELETE_NOT_ALLOWED = 111
    DELETION_OF_WHOLE_CONFIG_NOT_ALLOWED = 112
    INVALID_SECTION_PROVIDED = 113
    NO_BODY_PROVIDED = 114
    UCI_SET_ERROR = 115
    INVALID_QUERY_PARAMETER = 116
    GENERAL_CONFIGURATION_ERROR = 117

    # Authentication and authorization errors (120-123)
    UNAUTHORIZED_ACCESS = 120
    LOGIN_FAILED = 121
    GENERAL_STRUCTURE_INCORRECT = 122
    INVALID_JWT_TOKEN = 123

    # File upload errors (150-151)
    NOT_ENOUGH_FREE_SPACE = 150
    FILE_SIZE_TOO_BIG = 151


ERROR_DESCRIPTIONS: Dict[int, str] = {
    100: "Response not implemented",
    101: "No action provided",
    102: "Provided action is not available",
    103: "Invalid options",
    104: "UCI GET error",
    105: "UCI DELETE error",
    106: "UCI CREATE error",
    107: "Invalid structure",
    108: "Section creation is not allowed",
    109: "Name already used",
    110: "Name not provided",
    111: "DELETE not allowed",
    112: "Deletion of whole configuration is not allowed",
    113: "Invalid section provided",
    114: "No body provided for the request",
    115: "UCI SET error",
    116: "Invalid query parameter",
    117: "General configuration error",
    120: "Unauthorized access",
    121: "Login failed for any reason",
    122: "General structure of request is incorrect",
    123: "JWT token that is provided with authorization header is invalid",
    150: "Not enough free space in the device (when uploading files)",
    151: "File size is bigger than the maximum size allowed (when uploading files)",
}
