# Create and train the model
from model import ForestFireModel

model = ForestFireModel(data_url="dataset.csv")  # ← Use your actual CSV filename
model.train()

# Export to .mlmodel
model.export_to_coreml("FirePredictor.mlmodel")
