class Model:
    """Sample model class."""
    def __init__(self, identifier):
        self.identifier = identifier

    def process(self):
        """Process model data."""
        return f"Processed {self.identifier}"
