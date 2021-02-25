"""
Wrappers for information to be passed around. Should contain all the info
needed by classifiers and other ml module components.
"""


class Capsule:
    """
    Encapsulates main sentence info needed for ml module components.

    NOTE: this class is a reduced and simplified version of the original Capsule
    class from dogbone, and it does not provide any preprocessing functionality.
    """

    def __init__(self, text, flags=None):
        # Sentence text
        self.text = text
        # List of flags
        self.flags = flags or []
