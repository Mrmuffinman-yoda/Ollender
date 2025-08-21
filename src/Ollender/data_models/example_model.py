class DataModel:
    """Sample data model class."""
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def display(self):
        """Display model information."""
        return f"{self.name}: {self.value}"
